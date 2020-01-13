/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')

chai.should()
chai.use(sinonChai)
const { expect } = chai

const Helpers = require('../helpers/esSourceHelpers')
const { V3Work } = require('../lib/v3Work')

describe('v3 work retrieval tests', () => {
  describe('parseWork()', () => {
    let testWork
    let mockGet
    let mockLoad
    beforeEach(() => {
      testWork = new V3Work(sinon.mock(), {})
      mockGet = sinon.stub(V3Work, 'getInstanceOrEditions')
      mockLoad = sinon.stub(V3Work.prototype, 'loadWork')
    })

    afterEach(() => {
      mockGet.restore()
      mockLoad.restore()
    })

    it('should load work from database given ElasticSearch query', (done) => {
      mockLoad.returns('dbWork')
      mockGet.returns('fetchWork')
      const outWork = testWork.parseWork('newWork', { recordType: 'testing' })
      expect(mockGet).to.be.calledOnceWith('newWork')
      expect(mockLoad).to.be.calledOnceWith('fetchWork', 'testing')
      expect(outWork).to.equal('dbWork')
      done()
    })

    it('should set recordType to editions if not provided', (done) => {
      mockLoad.returns('dbWork')
      mockGet.returns('fetchWork')
      const outWork = testWork.parseWork('newWork', {})
      expect(mockGet).to.be.calledOnceWith('newWork')
      expect(mockLoad).to.be.calledOnceWith('fetchWork', 'editions')
      expect(outWork).to.equal('dbWork')
      done()
    })
  })

  describe('loadWork()', () => {
    let testWork
    let mockGet
    let mockIds
    let mockAgents
    let mockLinks
    let mockDates
    let esWork
    beforeEach(() => {
      testWork = new V3Work(sinon.mock(), {})
      mockGet = sinon.stub(V3Work.prototype, 'getWork')
      mockIds = sinon.stub(V3Work.prototype, 'getIdentifiers')
      mockAgents = sinon.stub(Helpers, 'parseAgents')
      mockLinks = sinon.stub(Helpers, 'parseLinks')
      mockDates = sinon.stub(Helpers, 'parseDates')
      esWork = {
        uuid: 'testUUID',
        edition_range: '2019',
        instanceIds: [
          {
            instance_id: 1,
            edition_id: 1,
          }, {
            instance_id: 2,
            edition_id: 1,
          }, {
            instance_id: 3,
            edition_id: 2,
          },
        ],
      }
    })

    afterEach(() => {
      mockGet.restore()
      mockIds.restore()
      mockAgents.restore()
      mockLinks.restore()
      mockDates.restore()
    })
    it('should load work from database given parameters', async () => {
      mockGet.returns({ id: 1 })
      mockIds.returns([1, 2, 3])

      const mockGetEditions = sinon.stub(V3Work.prototype, 'getEditions')
      mockGetEditions.returns(['ed1', 'ed2'])

      const dbWork = await testWork.loadWork(esWork, 'editions')
      expect(dbWork.id).to.equal(1)
      expect(dbWork.edition_range).to.equal('2019')
      expect(dbWork.identifiers[1]).to.equal(2)
      expect(dbWork.editions[0]).to.equal('ed1')
      expect(dbWork.instances).to.equal(null)
      expect(mockGetEditions).to.be.calledOnceWith([1, 2])
      mockGetEditions.restore()
    })

    it('should load work from database with instances if specified', async () => {
      mockGet.returns({ id: 1 })
      mockIds.returns([1, 2, 3])

      const mockGetEditions = sinon.stub(V3Work.prototype, 'getInstances')
      mockGetEditions.returns(['inst1', 'inst2', 'inst3'])

      const dbWork = await testWork.loadWork(esWork, 'instances')
      expect(dbWork.id).to.equal(1)
      expect(dbWork.edition_range).to.equal('2019')
      expect(dbWork.identifiers[1]).to.equal(2)
      expect(dbWork.instances[2]).to.equal('inst3')
      expect(dbWork.editions).to.equal(null)
      expect(mockGetEditions).to.be.calledOnceWith([1, 2, 3])
      mockGetEditions.restore()
    })
  })

  describe('getInstanceOrEditions()', () => {
    let mockFormatRange
    beforeEach(() => {
      mockFormatRange = sinon.stub(Helpers, 'formatSingleResponseEditionRange')
    })

    afterEach(() => {
      mockFormatRange.restore()
    })

    it('should filter inner records if inner_hits is present', (done) => {
      const testResp = {
        _index: 'sfr_test',
        _type: 'test',
        _id: 1,
        _score: 1,
        _source: {
          instances: [
            {
              id: 1,
              pub_date: '2000',
              instance_id: 10,
              edition_id: 11,
            },
            { id: 2, pub_place: 'Testtown' },
            {
              id: 3,
              formats: ['test1'],
              instance_id: 41,
              edition_id: 42,
            },
            { id: 4 },
          ],
        },
        inner_hits: {
          testing: {
            hits: {
              hits: [
                { _nested: { offset: 0 } },
                { _nested: { offset: 2 } },
              ],
            },
          },
        },
      }

      const fetchObjects = V3Work.getInstanceOrEditions(testResp)
      // eslint-disable-next-line no-unused-expressions
      expect(mockFormatRange).to.be.calledOnce
      expect(fetchObjects.uuid).to.equal(1)
      expect(fetchObjects.instanceIds[0].instance_id).to.equal(10)
      expect(fetchObjects.instanceIds[1].edition_id).to.equal(42)
      done()
    })

    it('should remove any empty instance records', (done) => {
      const testResp = {
        _index: 'sfr_test',
        _type: 'test',
        _id: 1,
        _score: 1,
        _source: {
          instances: [
            {
              id: 2,
              pub_place: 'Testtown',
              instance_id: 102,
              edition_id: 103,
            },
            {
              id: 1,
              pub_date: '2000',
              instance_id: 10,
              edition_id: 11,
            },
            { id: 4 },
            {
              id: 3,
              formats: ['test1'],
              instance_id: 41,
              edition_id: 42,
            },
          ],
        },
      }

      const fetchObjects = V3Work.getInstanceOrEditions(testResp)
      // eslint-disable-next-line no-unused-expressions
      expect(mockFormatRange).to.be.calledOnce
      expect(fetchObjects.uuid).to.equal(1)
      expect(fetchObjects.instanceIds.length).to.equal(3)
      expect(fetchObjects.instanceIds[0].instance_id).to.equal(102)
      expect(fetchObjects.instanceIds[1].edition_id).to.equal(11)
      done()
    })
  })
})
