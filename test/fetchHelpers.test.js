/* eslint-disable semi, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import chaiFs from 'chai-fs'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import Helpers from '../src/fetchHelpers.js'
chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
chai.use(chaiFs)
const expect = chai.expect

describe('Fetch Helpers [fetchHelpers.js]', () => {
  beforeEach(() => {
    // fileStub = sinon.stub(csvtojson(), 'fromFile')
  })

  afterEach(() => {
    // fileStub.restore()
  })

  describe('exports.sleep', () => {
    it('should sleep for 10 seconds', async () => {
      let success = 1
      try {
        await Helpers.sleep(500, 0)
      } catch (e) {
        success = 0
      }
      expect(success).to.equal(1)
    })
  })

  describe('exports.loadFromCSV', () => {
    it('should verify existence of the lc_relators.csv file', () => {
      expect('./data/lc_relators.csv').to.be.a.path()
    })

    it('should process a list of objects from the csvfile', async () => {
      let rows = await Helpers.loadFromCSV()
      expect(rows).to.have.lengthOf(268)
      expect(rows).to.deep.include(['aut', 'author'])
    })
  })

  describe('exports.loadLCRels', () => {
    it('should parse CSV contents into an array', async () => {
      var csvStub = sinon.stub(Helpers, 'loadFromCSV')
      csvStub.resolves([['aut', 'author']])
      let results = await Helpers.loadLCRels()
      expect(JSON.stringify(results)).to.equal(JSON.stringify([['aut', 'author']]))
      csvStub.restore()
    })

    it('should throw an error if CSV cannot be parsed', async () => {
      var csvStub = sinon.stub(Helpers, 'loadFromCSV')
      csvStub.rejects(new Error())
      try {
        let results = await Helpers.loadLCRels()
      } catch (err) {
        expect(err).to.be.instanceof(Error)
        expect(err.message).to.equal('Unable to load LC Relations from CSV file')
      }
      csvStub.restore()
    })
  })
})
