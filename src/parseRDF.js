import { parseString } from 'xml2js'
import moment from 'moment'

import logger from './helpers/logger'

import { WorkRecord, InstanceRecord, Agent, Identifier, Format, Subject, Link, Measurement, Rights } from './sfrMetadataModel'

const storeFields = [
  ['dcterms:title', 'title'],
  ['dcterms:alternative', 'alt_titles'],
  ['dcterms:publisher', 'publisher'],
  ['dcterms:rights', 'rights_statement'],
  ['pgterms:marc010', 'lccn'],
  ['pgterms:marc901', 'coverImageUrl']
]

const workFields = [
  'title',
  'alt_titles'
]

const entityFields = [
  ['pgterms:name', 'name']
]

const fileFields = [
  ['dcterms:modified', 'modified'],
  ['dcterms:extent', 'size']
]

const subjAuthRegex = /\/([A-Z]+)$/

// This is the handler function for this stage in the fetcher script
// It takes a raw object containing RDF text and converts this
// into a parsed Object that conforms with the SFR Metadata Model
exports.parseRDF = (data, gutenbergID, gutenbergURI, lcRels, callback) => {

  // Load RDF string from source object
  let rdfData = data['data']['repository']['object']
  let rdfText = rdfData['text']
  // Read XML/RDF string into javascript object
  parseString(rdfText, (err, result) => {

    if (err) return callback(err, null)

    // On success, parse resulting object into Metadata Model Object
    let gutenbergData = exports.loadGutenbergRecord(result['rdf:RDF'], gutenbergID, lcRels)
    callback(null, gutenbergData)
  })
}


// This does the transformation work from RDF to the SFR standard
// It relies on models imported from sfrMetadataModel, which defines each
// type of record created here
exports.loadGutenbergRecord = (rdf, gutenbergID, lcRels) => {

  // Load main metadata blocks from RDF
  let ebook = rdf['pgterms:ebook'][0]
  let work = rdf['cc:Work'][0]

  // Create a new work record, where all metadata will be stored
  let bibRecord = new WorkRecord()

  // Load basic Fields
  let mainFields = {}
  storeFields.map(field => {
    mainFields[field[1]] = exports.getRecordField(ebook, field[0])
  })

  // Load language
  let languageCont = ebook['dcterms:language'][0]['rdf:Description'][0]
  let language = exports.getRecordField(languageCont, 'rdf:value')
  bibRecord.language = language

  // Add fields to work Record
  workFields.map(field => {
    bibRecord[field] = mainFields[field]
  })
  bibRecord.language = language

  // Add Subjects to the work
  bibRecord.subjects = exports.getSubjects(ebook['dcterms:subject'])

  // Add Agents to the work
  bibRecord.agents = exports.getAgents(ebook, lcRels)

  // Add a rights statement to the work
  const license = exports.getFieldAttrib(work['cc:license'][0], 'rdf:resource')
  const rightsStmt = new Rights('gutenberg', license, mainFields.rights_statement, '')
  bibRecord.rights.push(rightsStmt)
  // Add dates to the work
  if ('dcterms:issued' in ebook) {
    let issued = exports.getRecordField(ebook, 'dcterms:issued')
    bibRecord.addDate(issued, issued, 'issued')
  }
  // Add the gutenberg ID, which is also assigned as the primary identifier
  bibRecord.addIdentifier('gutenberg', gutenbergID, 1)
  bibRecord.primary_identifier = new Identifier('gutenberg', gutenbergID, 1)

  // If present, add LCCN identifier to the work
  if (mainFields['lccn'] !== '') bibRecord.addIdentifier('lccn', mainFields['lccn'], 1)

  // Create an instance (which is what this Gutenberg record really is)
  bibRecord.addInstance(mainFields['title'], language)
  let gutenbergInstance = bibRecord.instances[0]

  // Add formats to the instance
  gutenbergInstance.formats = exports.getFormats(ebook['dcterms:hasFormat'], bibRecord.license)
  gutenbergInstance.formats.map(format => {
    format.addIdentifier('gutenberg', gutenbergID, 1)
  })

  // Add Publisher to instance
  gutenbergInstance.addAgent('Project Gutenberg', ['publisher'], null, null, null, null)

  // Add the gutenberg ID to this instance since it is our only ID for it
  gutenbergInstance.addIdentifier('gutenberg', gutenbergID, 1)

  // Add rights information to instance and child items
  gutenbergInstance.rights.push(rightsStmt)
  gutenbergInstance.formats.map(item => {
    item.rights.push(rightsStmt)
  })

  return bibRecord
}

// Load agents from the RDF block
// This loads the special "creator" field as well as the arbitrarily defined
// marcrel relationships, which it scans the document for
exports.getAgents = (ebook, lcRels) => {

  let agents = []

  // Try to load a creator. Not all RDF files have creators associated, so
  // this will catch any error if it does not exist
  try {

    let creator = exports.getAgent(ebook['dcterms:creator'][0]['pgterms:agent'][0], 'author')
    agents.push(creator)

  } catch (e) {

    if (e instanceof TypeError) logger.notice('No creator associated')
    else throw e

  }

  // Search RDF document for all marcrel relationships and create Agents
  lcRels.map((rel) => {

    let roleTerm = 'marcrel:' + rel[0]

    if (roleTerm in ebook) {
      let ent = exports.getAgent(ebook[roleTerm][0]['pgterms:agent'][0], rel[1])
      agents.push(ent)
    }

  })

  return agents
}


// This function explicitly creates each agent
exports.getAgent = (agent, role) => {

  // By default we know the role, and likely do not have a website/link
  let entRec = {
    'role': role,
    'webpage': null
  }

  // Load the fields we will be storing, as defined at the top of this file
  entityFields.map(field => {
    entRec[field[1]] = exports.getRecordField(agent, field[0])
  })

  // Aliases is an array, so it should be stored as such
  entRec['aliases'] = agent['pgterms:alias']
  // If a webpage exists, create a Link object for that page
  if ('pgterms:webpage' in agent) {
    let pageLink = exports.getFieldAttrib(agent['pgterms:webpage'][0], 'rdf:resource')
    entRec['link'] = new Link(pageLink, 'text/html', 'description')
  }

  let newAgent = new Agent(entRec['name'], [entRec['role']], entRec['aliases'], entRec['link'])

  if ('pgterms:birthdate' in agent) {
    let birth = exports.getRecordField(agent, 'pgterms:birthdate')
    newAgent.addDate(birth, birth, 'birth_date')
  }

  if ('pgterms:deathdate' in agent) {
    let death = exports.getRecordField(agent, 'pgterms:deathdate')
    newAgent.addDate(death, death, 'death_date')
  }

  return newAgent
}

exports.getSubjects = (subjects) => {

  let terms = []
  if (!subjects) return terms

  subjects.map(subject => {
    let subjRecord = subject['rdf:Description'][0]
    let authURL = exports.getFieldAttrib(subjRecord['dcam:memberOf'][0], 'rdf:resource')
    let authority = subjAuthRegex.exec(authURL)[1]
    let term = exports.getRecordField(subjRecord, 'rdf:value')

    let sfrSubject = new Subject(authority, term, 1)

    terms.push(sfrSubject)
  })

  return terms
}

exports.getFormats = (formats, license) => {
  let epubs = []

  if (!formats) return epubs

  formats.map(format => {

    let fileFormat = format['pgterms:file'][0]

    let url = exports.getFieldAttrib(fileFormat, 'rdf:about')

    if (url.includes('.epub')) {

      let epubLink = new Link(url, 'epub', 'ebook')
      let epub = {}

      fileFields.map(field => {
        epub[field[1]] = exports.getRecordField(fileFormat, field[0])
      })

      let sfrFormat = new Format('application/epub+zip', epubLink, epub['modified'])
      sfrFormat.addMeasurement('bytes', epub['size'], 1, moment().format())

      sfrFormat.source = 'gutenberg'
      sfrFormat.rights_uri = license

      epubs.push(sfrFormat)

    }
  })

  return epubs
}

exports.getRecordField = (rec, field) => {
  try {

    if (typeof rec[field][0] === 'object') return rec[field][0]._
    else return rec[field][0]

  } catch (e) {

    if (e instanceof TypeError) return ''
    else throw e

  }
}

exports.getFieldAttrib = (field, attrib) => {
  let attribs = field['$']
  return attribs[attrib]
}
