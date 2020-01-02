import Axios from 'axios'
import { parseString } from 'xml2js'
import moment from 'moment'

import logger from './helpers/logger'

import {
  WorkRecord, Agent, Identifier, Format, Subject, Link, Rights,
} from './sfrMetadataModel'

const storeFields = [
  ['dcterms:title', 'title'],
  ['dcterms:alternative', 'alt_titles'],
  ['dcterms:publisher', 'publisher'],
  ['dcterms:rights', 'rights_statement'],
  ['pgterms:marc010', 'lccn'],
  ['pgterms:marc901', 'coverImageUrl'],
]

const workFields = [
  'title',
  'alt_titles',
]

const entityFields = [
  ['pgterms:name', 'name'],
]

const fileFields = [
  ['dcterms:modified', 'modified'],
  ['dcterms:extent', 'size'],
]

const subjAuthRegex = /\/([A-Z]+)$/

// This is the handler function for this stage in the fetcher script
// It takes a raw object containing RDF text and converts this
// into a parsed Object that conforms with the SFR Metadata Model
exports.parseRDF = (data, gutenbergID, gutenbergURI, lcRels, callback) => {
  // Load RDF string from source object
  const rdfData = data.data.repository.object
  const rdfText = rdfData.text
  // Read XML/RDF string into javascript object
  parseString(rdfText, async (err, result) => {
    if (err) return callback(err, null)

    // On success, parse resulting object into Metadata Model Object
    const gutenbergData = await exports.loadGutenbergRecord(result['rdf:RDF'], gutenbergID, lcRels)
    callback(null, gutenbergData)
  })
}


// This does the transformation work from RDF to the SFR standard
// It relies on models imported from sfrMetadataModel, which defines each
// type of record created here
exports.loadGutenbergRecord = async (rdf, gutenbergID, lcRels) => {
  // Load main metadata blocks from RDF
  const ebook = rdf['pgterms:ebook'][0]
  const work = rdf['cc:Work'][0]

  // Create a new work record, where all metadata will be stored
  const bibRecord = new WorkRecord()

  // Load basic Fields
  const mainFields = {}
  storeFields.forEach((field) => {
    mainFields[field[1]] = exports.getRecordField(ebook, field[0])
  })

  // Load language
  const languageCont = ebook['dcterms:language'][0]['rdf:Description'][0]
  const language = exports.getRecordField(languageCont, 'rdf:value')
  bibRecord.language = language

  // Add fields to work Record
  workFields.forEach((field) => {
    bibRecord[field] = mainFields[field]
  })
  bibRecord.language = language

  // Add Subjects to the work
  bibRecord.subjects = exports.getSubjects(ebook['dcterms:subject'])

  // Add Agents to the work
  bibRecord.agents = await exports.getAgents(ebook, lcRels)

  // Add a rights statement to the work
  const license = exports.getFieldAttrib(work['cc:license'][0], 'rdf:resource')
  const rightsStmt = new Rights('gutenberg', license, mainFields.rights_statement, '')
  bibRecord.rights.push(rightsStmt)
  // Add dates to the work
  if ('dcterms:issued' in ebook) {
    const issued = exports.getRecordField(ebook, 'dcterms:issued')
    bibRecord.addDate(issued, issued, 'issued')
  }
  // Add the gutenberg ID, which is also assigned as the primary identifier
  bibRecord.addIdentifier('gutenberg', gutenbergID, 1)
  bibRecord.primary_identifier = new Identifier('gutenberg', gutenbergID, 1)

  // If present, add LCCN identifier to the work
  if (mainFields.lccn !== '') bibRecord.addIdentifier('lccn', mainFields.lccn, 1)

  // Create an instance (which is what this Gutenberg record really is)
  bibRecord.addInstance(mainFields.title, language)
  const gutenbergInstance = bibRecord.instances[0]

  // Add formats to the instance
  gutenbergInstance.formats = exports.getFormats(ebook['dcterms:hasFormat'], bibRecord.license, gutenbergID)
  gutenbergInstance.formats.forEach((format) => {
    format.addIdentifier('gutenberg', gutenbergID, 1)
  })

  // Add Publisher to instance
  gutenbergInstance.addAgent('Project Gutenberg', ['publisher'], null, null, null, null)

  // Add the gutenberg ID to this instance since it is our only ID for it
  gutenbergInstance.addIdentifier('gutenberg', gutenbergID, 1)

  // Add rights information to instance and child items
  gutenbergInstance.rights.push(rightsStmt)
  gutenbergInstance.formats.forEach((item) => {
    item.rights.push(rightsStmt)
  })

  return bibRecord
}

const getMARCRelAgents = async (rels, ebook) => {
  const agents = []
  for (let i = 0; i < rels.length; i++) {
    const roleTerm = `marcrel:${rels[i][0]}`

    if (roleTerm in ebook) {
      try {
        // eslint-disable-next-line no-await-in-loop
        const ent = await exports.getAgent(
          ebook[roleTerm][0]['pgterms:agent'][0], rels[i][1],
        )
        agents.push(ent)
      } catch (err) {
        // Do nothing
      }
    }
  }
  return agents
}

// Load agents from the RDF block
// This loads the special "creator" field as well as the arbitrarily defined
// marcrel relationships, which it scans the document for
exports.getAgents = async (ebook, lcRels) => {
  const agents = []

  // Try to load a creator. Not all RDF files have creators associated, so
  // this will catch any error if it does not exist
  try {
    const creator = await exports.getAgent(ebook['dcterms:creator'][0]['pgterms:agent'][0], 'author')
    agents.push(creator)
  } catch (e) {
    if (e instanceof TypeError) logger.notice('No creator associated')
    else throw e
  }

  // Search RDF document for all marcrel relationships and create Agents
  const relAgents = await getMARCRelAgents(lcRels, ebook)
  agents.push(...relAgents)

  return agents
}

const getAgentVIAF = async (newAgent, queryType) => {
  try {
    const resp = await Axios.get('https://dev-platform.nypl.org/api/v0.1/research-now/viaf-lookup', {
      params: {
        queryName: newAgent.name,
        queryType,
      },
    })
    const viafData = resp.data
    if ('viaf' in viafData) {
      newAgent.viaf = viafData.viaf
      newAgent.lcnaf = viafData.lcnaf
      if (viafData.name !== newAgent.name) {
        newAgent.aliases.push(newAgent.name)
        newAgent.name = viafData.name
      }
    }
  } catch (err) {
    // Nothing to do, just skip the enhancement
  }

  return true
}

// This function explicitly creates each agent
exports.getAgent = async (agent, role) => {
  // By default we know the role, and likely do not have a website/link
  const entRec = { role, webpage: null }

  // Load the fields we will be storing, as defined at the top of this file
  entityFields.forEach((field) => {
    entRec[field[1]] = exports.getRecordField(agent, field[0])
  })

  // Aliases is an array, so it should be stored as such
  entRec.aliases = agent['pgterms:alias']
  // If a webpage exists, create a Link object for that page
  if ('pgterms:webpage' in agent) {
    const pageLink = exports.getFieldAttrib(agent['pgterms:webpage'][0], 'rdf:resource')
    const bioFlags = { local: false, download: false, ebook: false }
    entRec.link = new Link(pageLink, 'text/html', bioFlags)
  }

  const newAgent = new Agent(entRec.name, [entRec.role], entRec.aliases, entRec.link)

  if ('pgterms:birthdate' in agent) {
    const birth = exports.getRecordField(agent, 'pgterms:birthdate')
    newAgent.addDate(birth, birth, 'birth_date')
  }

  if ('pgterms:deathdate' in agent) {
    const death = exports.getRecordField(agent, 'pgterms:deathdate')
    newAgent.addDate(death, death, 'death_date')
  }

  const corporateRoles = ['publisher', 'manufacturer']
  const queryType = corporateRoles.indexOf(role) > -1 ? 'corporate' : 'personal'

  await getAgentVIAF(newAgent, queryType)

  return newAgent
}

exports.getSubjects = (subjects) => {
  const terms = []
  if (!subjects) return terms

  subjects.forEach((subject) => {
    const subjRecord = subject['rdf:Description'][0]
    const authURL = exports.getFieldAttrib(subjRecord['dcam:memberOf'][0], 'rdf:resource')
    const authority = subjAuthRegex.exec(authURL)[1]
    const term = exports.getRecordField(subjRecord, 'rdf:value')

    const sfrSubject = new Subject(authority, term, 1)

    terms.push(sfrSubject)
  })

  return terms
}

exports.getFormats = (formats, license, gutenbergID) => {
  const epubs = []

  if (!formats) return epubs

  formats.forEach((format) => {
    const fileFormat = format['pgterms:file'][0]
    const url = exports.getFieldAttrib(fileFormat, 'rdf:about')
    if (url.includes('.epub')) {
      const epubImages = !url.includes('noimages')
      const epubFlags = {
        local: false, download: true, ebook: true, images: epubImages,
      }
      const epubLink = new Link(url, 'application/epub+zip', epubFlags)
      const epub = {}

      fileFields.forEach((field) => {
        epub[field[1]] = exports.getRecordField(fileFormat, field[0])
      })

      const sfrFormat = new Format('application/epub+zip', epubLink, epub.modified)
      sfrFormat.addMeasurement('bytes', epub.size, 1, moment().format(), gutenbergID)

      sfrFormat.source = 'gutenberg'

      epubs.push(sfrFormat)
    }
  })

  return epubs
}

exports.getRecordField = (rec, field) => {
  try {
    if (typeof rec[field][0] === 'object') return rec[field][0]._
    return rec[field][0]
  } catch (e) {
    if (e instanceof TypeError) return ''
    throw e
  }
}

exports.getFieldAttrib = (field, attrib) => {
  const attribs = field.$
  return attribs[attrib]
}
