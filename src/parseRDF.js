import { parseString } from 'xml2js'

const storeFields = [
  ['dcterms:title', 'title'],
  ['dcterms:alternative', 'altTitle'],
  ['dcterms:publisher', 'publisher'],
  ['dcterms:rights', 'rightsStmt'],
  ['pgterms:marc010', 'lccn'],
  ['dcterms:issued', 'created'],
  ['pgterms:marc901', 'coverImageUrl']
]

const entityFields = [
  ['pgterms:birthdate', 'birth'],
  ['pgterms:deathdate', 'death'],
  ['pgterms:name', 'name']
]

const fileFields = [
  ['dcterms:modified', 'updated'],
  ['dcterms:extent', 'size']
]

const subjAuthRegex = /\/([A-Z]+)$/

exports.parseRDF = (data, lcRels, callback) => {
  let rdfData = data['data']['repository']['object']
  let rdfText = rdfData['text']
  parseString(rdfText, (err, result) => {
    if (err) return callback(err, null)
    let gutenbergData = exports.loadGutenbergRecord(result['rdf:RDF'], lcRels)
    callback(null, gutenbergData)
  })
}

exports.loadGutenbergRecord = (rdf, lcRels) => {
  let bibRecord = {}
  let ebook = rdf['pgterms:ebook'][0]
  let work = rdf['cc:Work'][0]

  bibRecord['formats'] = exports.getFormats(ebook['dcterms:hasFormat'])
  bibRecord['subjects'] = exports.getSubjects(ebook['dcterms:subject'])
  bibRecord['entities'] = exports.getEntities(ebook, lcRels)
  storeFields.map(field => {
    bibRecord[field[1]] = exports.getRecordField(ebook, field[0])
  })
  bibRecord['license'] = exports.getFieldAttrib(work['cc:license'][0], 'rdf:resource')
  let languageCont = ebook['dcterms:language'][0]['rdf:Description'][0]
  bibRecord['language'] = exports.getRecordField(languageCont, 'rdf:value')
  return bibRecord
}

exports.getEntities = (ebook, lcRels) => {
  let entities = []
  try {
    let creator = exports.getEntity(ebook['dcterms:creator'][0]['pgterms:agent'][0], 'author')
    entities.push(creator)
  } catch (e) {
    if (e instanceof TypeError) {
      console.log('No creator associated')
    } else {
      throw e
    }
  }
  lcRels.map((rel) => {
    let roleTerm = 'marcrel:' + rel[0]
    if (roleTerm in ebook) {
      let ent = exports.getEntity(ebook[roleTerm][0]['pgterms:agent'][0], rel[1])
      entities.push(ent)
    }
  })
  return entities
}

exports.getEntity = (entity, role) => {
  let entRec = {
    'role': role
  }
  entityFields.map(field => {
    entRec[field[1]] = exports.getRecordField(entity, field[0])
  })

  entRec['aliases'] = entity['pgterms:alias']
  if ('pgterms:webpage' in entity) {
    entRec['webpage'] = exports.getFieldAttrib(entity['pgterms:webpage'][0], 'rdf:resource')
  }
  return entRec
}

exports.getSubjects = (subjects) => {
  let terms = []
  if (!subjects) return terms
  subjects.map(subject => {
    let subjRecord = subject['rdf:Description'][0]
    let authURL = exports.getFieldAttrib(subjRecord['dcam:memberOf'][0], 'rdf:resource')

    let term = {
      'term': exports.getRecordField(subjRecord, 'rdf:value'),
      'authority': subjAuthRegex.exec(authURL)[1]
    }
    terms.push(term)
  })
  return terms
}

exports.getFormats = (formats) => {
  let epubs = []
  if (!formats) return epubs
  formats.map(format => {
    let fileFormat = format['pgterms:file'][0]
    let url = exports.getFieldAttrib(fileFormat, 'rdf:about')
    if (url.includes('.epub')) {
      let epub = {
        'url': url
      }
      fileFields.map(field => {
        epub[field[1]] = exports.getRecordField(fileFormat, field[0])
      })
      epubs.push(epub)
    }
  })
  return epubs
}

exports.getRecordField = (rec, field) => {
  try {
    if (typeof rec[field][0] === 'object') {
      return rec[field][0]._
    } else {
      return rec[field][0]
    }
  } catch (e) {
    if (e instanceof TypeError) {
      return ''
    } else {
      throw e
    }
  }
}

exports.getFieldAttrib = (field, attrib) => {
  let attribs = field['$']
  return attribs[attrib]
}
