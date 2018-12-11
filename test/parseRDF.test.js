/* eslint-disable semi, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import RDFParser from '../src/parseRDF.js'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

describe('RDF Parser [parseRDF.js]', () => {
  const testData = {
    'data': {
      'repository': {
        'object': {
          'text':
                  `
                    <?xml version="1.0" encoding="utf-8"?>
                    <rdf:RDF xml:base="http://www.gutenberg.org/"
                      xmlns:cc="http://web.resource.org/cc/"
                      xmlns:dcam="http://purl.org/dc/dcam/"
                      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                      xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
                      xmlns:dcterms="http://purl.org/dc/terms/"
                      xmlns:pgterms="http://www.gutenberg.org/2009/pgterms/"
                    >
                      <pgterms:ebook rdf:about="ebooks/6248">
                        <pgterms:downloads rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">0</pgterms:downloads>
                        <dcterms:hasFormat>
                          <pgterms:file rdf:about="http://www.gutenberg.org/ebooks/6248.epub.images">
                            <dcterms:format>
                              <rdf:Description rdf:nodeID="Nee6588f09c0649cf9486a8a25d04a6fe">
                                <dcam:memberOf rdf:resource="http://purl.org/dc/terms/IMT"/>
                                <rdf:value rdf:datatype="http://purl.org/dc/terms/IMT">application/epub+zip</rdf:value>
                              </rdf:Description>
                            </dcterms:format>
                            <dcterms:isFormatOf rdf:resource="ebooks/6248"/>
                            <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2018-10-28T13:20:08.823859</dcterms:modified>
                            <dcterms:extent rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">47995</dcterms:extent>
                          </pgterms:file>
                        </dcterms:hasFormat>
                        <dcterms:rights>Public domain in the USA.</dcterms:rights>
                        <dcterms:subject>
                          <rdf:Description rdf:nodeID="Ne41bbb52df5f4dbf98b4ab783ed42c34">
                            <dcam:memberOf rdf:resource="http://purl.org/dc/terms/LCC"/>
                            <rdf:value>PS</rdf:value>
                          </rdf:Description>
                        </dcterms:subject>
                        <dcterms:publisher>Project Gutenberg</dcterms:publisher>
                        <dcterms:type>
                          <rdf:Description rdf:nodeID="Ncf637b5118f74aad940dbfd983af9ef9">
                            <dcam:memberOf rdf:resource="http://purl.org/dc/terms/DCMIType"/>
                            <rdf:value>Text</rdf:value>
                          </rdf:Description>
                        </dcterms:type>
                        <dcterms:issued rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2004-08-01</dcterms:issued>
                        <dcterms:hasFormat>
                          <pgterms:file rdf:about="http://www.gutenberg.org/ebooks/6248.epub.noimages">
                            <dcterms:format>
                              <rdf:Description rdf:nodeID="N192c343cdd614778b2be088b6222c968">
                                <dcam:memberOf rdf:resource="http://purl.org/dc/terms/IMT"/>
                                <rdf:value rdf:datatype="http://purl.org/dc/terms/IMT">application/epub+zip</rdf:value>
                              </rdf:Description>
                            </dcterms:format>
                            <dcterms:isFormatOf rdf:resource="ebooks/6248"/>
                            <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2018-10-28T13:20:08.867863</dcterms:modified>
                            <dcterms:extent rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">47995</dcterms:extent>
                          </pgterms:file>
                        </dcterms:hasFormat>
                        <dcterms:creator>
                          <pgterms:agent rdf:about="2009/agents/1285">
                            <pgterms:birthdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1862</pgterms:birthdate>
                            <pgterms:alias>Parker, Gilbert, Sir, bart.</pgterms:alias>
                            <pgterms:webpage rdf:resource="http://en.wikipedia.org/wiki/Gilbert_Parker"/>
                            <pgterms:name>Parker, Gilbert</pgterms:name>
                            <pgterms:alias>Parker, Horatio Gilbert</pgterms:alias>
                            <pgterms:deathdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1932</pgterms:deathdate>
                          </pgterms:agent>
                        </dcterms:creator>
                        <dcterms:license rdf:resource="license"/>
                        <dcterms:language>
                          <rdf:Description rdf:nodeID="Nec9eb8e544184a32abd81186ed79f05b">
                            <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">en</rdf:value>
                          </rdf:Description>
                        </dcterms:language>
                        <dcterms:title>Michel and Angele [A Ladder of Swords], Volume 1.</dcterms:title>
                      </pgterms:ebook>
                      <cc:Work rdf:about="">
                        <rdfs:comment>Archives containing the RDF files for *all* our books can be downloaded at
                                http://www.gutenberg.org/wiki/Gutenberg:Feeds#The_Complete_Project_Gutenberg_Catalog</rdfs:comment>
                        <cc:license rdf:resource="https://creativecommons.org/publicdomain/zero/1.0/"/>
                      </cc:Work>
                      <rdf:Description rdf:about="http://en.wikipedia.org/wiki/Gilbert_Parker">
                        <dcterms:description>en.wikipedia</dcterms:description>
                      </rdf:Description>
                    </rdf:RDF>
                  `
        }
      }
    }
  }

  const testLC = [
    ['aut', 'author']
  ]

  const jsonInput = JSON.parse('{"$":{"xml:base":"http://www.gutenberg.org/","xmlns:cc":"http://web.resource.org/cc/","xmlns:dcam":"http://purl.org/dc/dcam/","xmlns:rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#","xmlns:rdfs":"http://www.w3.org/2000/01/rdf-schema#","xmlns:dcterms":"http://purl.org/dc/terms/","xmlns:pgterms":"http://www.gutenberg.org/2009/pgterms/"},"pgterms:ebook":[{"$":{"rdf:about":"ebooks/6248"},"pgterms:downloads":[{"_":"0","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#integer"}}],"dcterms:hasFormat":[{"pgterms:file":[{"$":{"rdf:about":"http://www.gutenberg.org/ebooks/6248.epub.images"},"dcterms:format":[{"rdf:Description":[{"$":{"rdf:nodeID":"Nee6588f09c0649cf9486a8a25d04a6fe"},"dcam:memberOf":[{"$":{"rdf:resource":"http://purl.org/dc/terms/IMT"}}],"rdf:value":[{"_":"application/epub+zip","$":{"rdf:datatype":"http://purl.org/dc/terms/IMT"}}]}]}],"dcterms:isFormatOf":[{"$":{"rdf:resource":"ebooks/6248"}}],"dcterms:modified":[{"_":"2018-10-28T13:20:08.823859","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#dateTime"}}],"dcterms:extent":[{"_":"47995","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#integer"}}]}]},{"pgterms:file":[{"$":{"rdf:about":"http://www.gutenberg.org/ebooks/6248.epub.noimages"},"dcterms:format":[{"rdf:Description":[{"$":{"rdf:nodeID":"N192c343cdd614778b2be088b6222c968"},"dcam:memberOf":[{"$":{"rdf:resource":"http://purl.org/dc/terms/IMT"}}],"rdf:value":[{"_":"application/epub+zip","$":{"rdf:datatype":"http://purl.org/dc/terms/IMT"}}]}]}],"dcterms:isFormatOf":[{"$":{"rdf:resource":"ebooks/6248"}}],"dcterms:modified":[{"_":"2018-10-28T13:20:08.867863","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#dateTime"}}],"dcterms:extent":[{"_":"47995","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#integer"}}]}]}],"dcterms:rights":["Public domain in the USA."],"dcterms:subject":[{"rdf:Description":[{"$":{"rdf:nodeID":"Ne41bbb52df5f4dbf98b4ab783ed42c34"},"dcam:memberOf":[{"$":{"rdf:resource":"http://purl.org/dc/terms/LCC"}}],"rdf:value":["PS"]}]}],"dcterms:publisher":["Project Gutenberg"],"dcterms:type":[{"rdf:Description":[{"$":{"rdf:nodeID":"Ncf637b5118f74aad940dbfd983af9ef9"},"dcam:memberOf":[{"$":{"rdf:resource":"http://purl.org/dc/terms/DCMIType"}}],"rdf:value":["Text"]}]}],"dcterms:issued":[{"_":"2004-08-01","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#date"}}],"dcterms:creator":[{"pgterms:agent":[{"$":{"rdf:about":"2009/agents/1285"},"pgterms:birthdate":[{"_":"1862","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#integer"}}],"pgterms:alias":["Parker, Gilbert, Sir, bart.","Parker, Horatio Gilbert"],"pgterms:webpage":[{"$":{"rdf:resource":"http://en.wikipedia.org/wiki/Gilbert_Parker"}}],"pgterms:name":["Parker, Gilbert"],"pgterms:deathdate":[{"_":"1932","$":{"rdf:datatype":"http://www.w3.org/2001/XMLSchema#integer"}}]}]}],"dcterms:license":[{"$":{"rdf:resource":"license"}}],"dcterms:language":[{"rdf:Description":[{"$":{"rdf:nodeID":"Nec9eb8e544184a32abd81186ed79f05b"},"rdf:value":[{"_":"en","$":{"rdf:datatype":"http://purl.org/dc/terms/RFC4646"}}]}]}],"dcterms:title":["Michel and Angele [A Ladder of Swords], Volume 1."]}],"cc:Work":[{"$":{"rdf:about":""},"rdfs:comment":["Archives containing the RDF files for *all* our books can be downloaded at http://www.gutenberg.org/wiki/Gutenberg:Feeds#The_Complete_Project_Gutenberg_Catalog"],"cc:license":[{"$":{"rdf:resource":"https://creativecommons.org/publicdomain/zero/1.0/"}}]}],"rdf:Description":[{"$":{"rdf:about":"http://en.wikipedia.org/wiki/Gilbert_Parker"},"dcterms:description":["en.wikipedia"]}]}')

  const jsonData = {
    'title': 'Michel and Angele [A Ladder of Swords], Volume 1.',
    'publisher': 'Project Gutenberg',
    'rightsStmt': 'Public domain in the USA.',
    'license': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'entities': [{
      'name': 'Parker, Gilbert',
      'aliases': ['Parker, Horatio Gilbert', 'Parker, Gilbert, Sir, bart.'],
      'birth': '1862',
      'death': '1932',
      'website': 'http://en.wikipedia.org/wiki/Gilbert_Parker',
      'role': 'author'
    }],
    'subjects': [{
      'term': 'PS',
      'authority': 'LCC'
    }],
    'formats': [
      {
        'url': 'http://www.gutenberg.org/ebooks/6248.epub.noimages',
        'updated': '2018-11-15',
        'size': '1235432'
      }, {
        'url': 'http://www.gutenberg.org/ebooks/6248.epub.images',
        'updated': '2018-11-15',
        'size': '21543253'
      }
    ]
  }

  describe('exports.parseRDF()', () => {
    it('should return data object with successful parse', () => {
      let gutStub = sinon.stub(RDFParser, 'loadGutenbergRecord')
      gutStub.returns(jsonData)
      RDFParser.parseRDF(testData, 1, 'https://gutenberg.org/1', testLC, (err, data) => {
        expect(data).to.not.equal(null)
        expect(data['title']).to.equal('Michel and Angele [A Ladder of Swords], Volume 1.')
      })
      gutStub.restore()
    })

    it('should return error if XML cannot be parsed', () => {
      let gutStub = sinon.stub(RDFParser, 'loadGutenbergRecord')
      let badXML = {
        'data': {
          'repository': {
            'object': {
              'text':
                      `
                        <?xml version="1.0" encoding="utf-8">
                        <dcterms:hasFormat>
                          <pgterms:file rdf:about="http://www.gutenberg.org/ebooks/6248.epub.noimages">
                            <dcterms:format>
                              <rdf:Description rdf:nodeID="N192c343cdd614778b2be088b6222c968">
                                <dcam:memberOf rdf:resource="http://purl.org/dc/terms/IMT"/>
                                <rdf:value rdf:datatype="http://purl.org/dc/terms/IMT">application/epub+zip</rdf:value>
                              </rdf:Description>
                            </dcterms:format>
                            <dcterms:isFormatOf rdf:resource="ebooks/6248"/>
                            <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2018-10-28T13:20:08.867863</dcterms:modified>
                            <dcterms:extent rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">47995</dcterms:extent>
                          </pgterms:file>
                        </dcterms:hasFormat>
                        <dcterms:creator>
                          <pgterms:agent rdf:about="2009/agents/1285">
                            <pgterms:birthdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1862</pgterms:birthdate>
                            <pgterms:alias>Parker, Gilbert, Sir, bart.</pgterms:alias>
                            <pgterms:webpage rdf:resource="http://en.wikipedia.org/wiki/Gilbert_Parker"/>
                            <pgterms:name>Parker, Gilbert</pgterms:name>
                            <pgterms:alias>Parker, Horatio Gilbert</pgterms:alias>
                            <pgterms:deathdate rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">1932</pgterms:deathdate>
                          </pgterms:agent>
                        </dcterms:creator>
                        <dcterms:license rdf:resource="license"/>
                        <dcterms:language>
                          <rdf:Description rdf:nodeID="Nec9eb8e544184a32abd81186ed79f05b">
                            <rdf:value rdf:datatype="http://purl.org/dc/terms/RFC4646">en</rdf:value>
                          </rdf:Description>
                        </dcterms:language>
                        <dcterms:title>Michel and Angele [A Ladder of Swords], Volume 1.</dcterms:title>
                      </pgterms:ebook>
                      <cc:Work rdf:about="">
                        <rdfs:comment>Archives containing the RDF files for *all* our books can be downloaded at
                                http://www.gutenberg.org/wiki/Gutenberg:Feeds#The_Complete_Project_Gutenberg_Catalog</rdfs:comment>
                        <cc:license rdf:resource="https://creativecommons.org/publicdomain/zero/1.0/"/>
                      </cc:Work>
                      <rdf:Description rdf:about="http://en.wikipedia.org/wiki/Gilbert_Parker">
                        <dcterms:description>en.wikipedia</dcterms:description>
                      </rdf:Description>
                      `
            }
          }
        }
      }
      RDFParser.parseRDF(badXML, 1, 'https://gutenberg.org/1', testLC, (err, data) => {
        expect(err).to.not.equal(null)
      })
      gutStub.restore()
    })
  })

  describe('exports.loadGutenbergRecord()', () => {
    it('should return a valid JSON object', () => {
      let formatStub = sinon.stub(RDFParser, 'getFormats')
      let subjectStub = sinon.stub(RDFParser, 'getSubjects')
      let entityStub = sinon.stub(RDFParser, 'getAgents')
      let fieldStub = sinon.stub(RDFParser, 'getRecordField')
      let attribStub = sinon.stub(RDFParser, 'getFieldAttrib')

      formatStub.returns(jsonData['formats'])

      subjectStub.returns(jsonData['subjects'])

      entityStub.returns(jsonData['entities'])

      fieldStub.returns('Test Value')

      attribStub.returns('Test Attrib')

      let parsedData = RDFParser.loadGutenbergRecord(jsonInput, testLC)
      expect(parsedData['title']).to.equal('Test Value')
      expect(parsedData['instances']).to.have.lengthOf(1)
      expect(parsedData['instances'][0]['formats']).to.have.lengthOf(2)
      expect(parsedData['agents'][0]['name']).to.equal('Parker, Gilbert')

      formatStub.restore()
      subjectStub.restore()
      entityStub.restore()
      fieldStub.restore()
      attribStub.restore()
    })
  })

  describe('exports.getAgents()', () => {
    let entStub = sinon.stub(RDFParser, 'getAgent')
    it('should return single entity for creator', () => {
      entStub.returns(jsonData['entities'][0])
      let creator = RDFParser.getAgents(jsonInput['pgterms:ebook'][0], testLC)
      expect(creator).to.have.lengthOf(1)
      expect(creator[0]['role']).to.equal('author')
      expect(creator[0]['name']).to.equal('Parker, Gilbert')
      entStub.restore()
    })

    it('should return empty array if no creator is found', () => {
      let jsonNoCreator = Object.assign({}, jsonInput['pgterms:ebook'][0])
      delete jsonNoCreator['dcterms:creator']
      let noCreator = RDFParser.getAgents(jsonNoCreator, testLC)
      expect(noCreator).to.have.lengthOf(0)
    })

    it('should return an entity for marcrel codes', () => {
      let jsonAutCreator = Object.assign({}, jsonInput['pgterms:ebook'][0])
      jsonAutCreator['marcrel:aut'] = jsonAutCreator['dcterms:creator']
      delete jsonAutCreator['dcterms:creator']
      let autCreator = RDFParser.getAgents(jsonAutCreator, testLC)
      expect(autCreator).to.have.lengthOf(1)
      expect(autCreator[0]['roles'][0]).to.equal('author')
      expect(autCreator[0]['name']).to.equal('Parker, Gilbert')
    })
  })

  describe('exports.getAgent()', () => {
    it('should return entity object', () => {
      let ent = jsonInput['pgterms:ebook'][0]['dcterms:creator'][0]['pgterms:agent'][0]
      let entity = RDFParser.getAgent(ent, 'author')
      expect(entity).to.include({ 'name': 'Parker, Gilbert'})
      expect(entity['roles'][0]).to.equal('author')
    })

    it('should include a webpage if it exists', () => {
      let ent = jsonInput['pgterms:ebook'][0]['dcterms:creator'][0]['pgterms:agent'][0]
      let entity = RDFParser.getAgent(ent, 'author')
      expect(entity['link']).to.include({'url': 'http://en.wikipedia.org/wiki/Gilbert_Parker' })
    })
  })

  describe('exports.getSubjects()', () => {
    it('should return an array of subjects', () => {
      let subjects = jsonInput['pgterms:ebook'][0]['dcterms:subject']
      let subjReturn = RDFParser.getSubjects(subjects)
      expect(subjReturn).to.have.lengthOf(1)
      expect(subjReturn[0]['value']).to.equal('PS')
      expect(subjReturn[0]['type']).to.equal('LCC')
    })
  })

  describe('exports.getFormats()', () => {
    let recStub, attribStub
    beforeEach(() => {
      recStub = sinon.stub(RDFParser, 'getRecordField')
      attribStub = sinon.stub(RDFParser, 'getFieldAttrib')
      recStub.returns('Test Value')
      attribStub.returns('something.epub')
    })

    afterEach(() => {
      recStub.restore()
      attribStub.restore()
    })
    it('should return an array of formats', () => {
      let formats = jsonInput['pgterms:ebook'][0]['dcterms:hasFormat']
      let formReturn = RDFParser.getFormats(formats)
      expect(formReturn).to.have.lengthOf(2)
      expect(formReturn[0]['link']['url']).to.equal('something.epub')
    })
  })

  describe('exports.getRecordField()', () => {
    it('should return a value for a field with a primitive value', () => {
      let testRec = { 'test': ['value'] }
      let testField = 'test'
      let testResp = RDFParser.getRecordField(testRec, testField)
      expect(testResp).to.equal('value')
    })

    it('should return a value for a field with an object', () => {
      let testRec = { 'test': [{ _: 'value', 'something': 'else' }] }
      let testField = 'test'
      let testResp = RDFParser.getRecordField(testRec, testField)
      expect(testResp).to.equal('value')
    })

    it('should return an empty string if field is not found', () => {
      let testRec = null
      let testField = 'test'
      let testResp = RDFParser.getRecordField(null, testField)
      expect(testResp).to.equal('')
    })
  })

  describe('exports.getFieldAttrib()', () => {
    it('should return a value if attrib exists', () => {
      let testField = { '$': { 'attrib1': 'attrib1' }, 'value': 'value' }
      let testAttrib = 'attrib1'
      let attribResp = RDFParser.getFieldAttrib(testField, testAttrib)
      expect(attribResp).to.equal('attrib1')
    })
  })
})
