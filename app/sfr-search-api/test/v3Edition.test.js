/* eslint-disable no-undef, no-unused-expressions */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')

chai.should()
chai.use(sinonChai)
const { expect } = chai

const Helpers = require('../helpers/esSourceHelpers')
const { V3Edition } = require('../lib/v3Edition')

describe('v3 edition retrieval tests', () => {
  describe('loadEdition()', () => {
    let testEdition
    let mockGet
    let mockParse
    let mockParseAgents
    let mockParseLinks
    let mockParseDates
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
      mockGet = sinon.stub(V3Edition.prototype, 'getEditions')
      mockParse = sinon.stub(V3Edition.prototype, 'parseEdition')
      mockParseAgents = sinon.stub(Helpers, 'parseAgents')
      mockParseLinks = sinon.stub(Helpers, 'parseLinks')
      mockParseDates = sinon.stub(Helpers, 'parseDates')
    })

    afterEach(() => {
      mockGet.restore()
      mockParse.restore()
      mockParseAgents.restore()
      mockParseLinks.restore()
      mockParseDates.restore()
    })

    it('should load work from database given edition identifier', async () => {
      mockGet.returns(['fetchEdition'])
      const outWork = await testEdition.loadEdition()
      expect(outWork).to.equal('fetchEdition')
      expect(mockGet).to.be.calledOnce
      expect(mockParse).to.be.calledOnce
      expect(mockParseAgents).to.be.calledOnceWith('fetchEdition', 'instances')
      expect(mockParseLinks).to.be.calledOnceWith('fetchEdition', 'instances')
      expect(mockParseDates).to.be.calledOnceWith('fetchEdition', 'instances')
    })

    it('should raise an error if no matching edition is found', async () => {
      mockGet.returns([])
      try {
        await testEdition.loadEdition()
      } catch (err) {
        expect(err.name).to.equal('NotFoundError')
      }
      expect(mockParse).to.be.not.calledOnce
    })
  })

  describe('getEditions()', () => {
    let testEdition
    let mockLoad
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
      testEdition.dbConn = sinon.mock()

      mockLoad = sinon.mock()
      testEdition.dbConn.loadEditions = mockLoad
    })

    it('should return an array of editions', (done) => {
      mockLoad.returns(['edition1'])
      const outEditions = testEdition.getEditions()
      expect(mockLoad).to.be.calledOnceWith([1], 1)
      expect(outEditions[0]).to.equal('edition1')
      done()
    })
  })

  describe('getInstances()', () => {
    let testEdition
    let mockLoad
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
      testEdition.dbConn = sinon.mock()

      mockLoad = sinon.mock()
      testEdition.dbConn.getEditionInstances = mockLoad
    })

    it('should return an array of editions', (done) => {
      mockLoad.returns(['inst1', 'inst2', 'inst3'])
      const outInstances = testEdition.getInstances()
      expect(mockLoad).to.be.calledOnceWith(1)
      expect(outInstances[1]).to.equal('inst2')
      done()
    })
  })

  describe('getIdentifiers()', () => {
    let testEdition
    let mockLoad
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
      testEdition.dbConn = sinon.mock()

      mockLoad = sinon.mock()
      testEdition.dbConn.loadIdentifiers = mockLoad
    })

    it('should return an array of identifiers', (done) => {
      mockLoad.returns(['id1', 'id2', 'id3'])
      const outIdentifiers = testEdition.getIdentifiers('instances', 1)
      expect(mockLoad).to.be.calledOnceWith('instances', 1)
      expect(outIdentifiers[1]).to.equal('id2')
      done()
    })
  })

  describe('parseEdition()', () => {
    let testEdition
    let mockSort
    let mockGetInstances
    let mockGetIdentifiers
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
      testEdition.edition = {}
      mockSort = sinon.stub(V3Edition.prototype, 'sortInstances')
      mockGetInstances = sinon.stub(V3Edition.prototype, 'getInstances')
      mockGetIdentifiers = sinon.stub(V3Edition.prototype, 'getIdentifiers')
    })

    afterEach(() => {
      mockSort.restore()
      mockGetInstances.restore()
      mockGetIdentifiers.restore()
    })

    it('should select best title by most common among the instances', async () => {
      mockGetInstances.returns([
        { title: 'Testing' }, { title: 'Not Testing' }, { title: 'Testing' },
      ])
      await testEdition.parseEdition()
      expect(testEdition.edition.title).to.equal('Testing')
      expect(mockSort).to.be.calledOnce
      expect(mockGetIdentifiers).callCount(3)
    })

    it('should parse a single year from the publication date range', async () => {
      mockGetInstances.returns([{ title: 'Testing' }])
      testEdition.edition.publication_date = '[2000-01-01,2000-12-31)'
      await testEdition.parseEdition()
      expect(testEdition.edition.title).to.equal('Testing')
      expect(testEdition.edition.publication_date).to.equal('2000')
      expect(mockSort).to.be.calledOnce
      expect(mockGetIdentifiers).to.be.calledOnce
    })

    it('should remove instances without items if showAll is false', async () => {
      testEdition.showAll = 'false'
      mockGetInstances.returns([
        { title: 'Testing', items: 'itemArray' },
        { title: 'Not Testing', items: null },
        { title: 'Testing', items: 'itemArray2' },
      ])
      await testEdition.parseEdition()
      expect(testEdition.edition.title).to.equal('Testing')
      expect(testEdition.edition.instances.length).to.equal(2)
      expect(mockSort).to.be.calledOnce
      expect(mockGetIdentifiers).callCount(2)
    })
  })

  describe('sortInstances()', () => {
    let testEdition
    beforeEach(() => {
      testEdition = new V3Edition(sinon.mock(), 1)
    })

    it('should sort the instances by numbers of holdings', (done) => {
      testEdition.edition = {
        instances: [
          { title: 'inst1', measurements: [{ value: 2 }] },
          { title: 'inst2', measurements: [{ value: 1 }] },
          { title: 'inst3', measurements: [{ value: 3 }] },
        ],
      }

      testEdition.sortInstances()

      expect(testEdition.edition.instances[0].title).to.equal('inst3')
      done()
    })

    it('should sort the instances by numbers of holdings & place featured instance first', (done) => {
      testEdition.edition = {
        items: [{ links: [{ url: 'featuredURL' }] }],
        instances: [
          { title: 'inst1', measurements: [{ value: 2 }], items: [{ links: [{ url: 'secondaryURL' }] }] },
          { title: 'inst2', measurements: [{ value: 1 }], items: [{ links: [{ url: 'featuredURL' }] }] },
          { title: 'inst3', measurements: [{ value: 3 }] },
        ],
      }

      testEdition.sortInstances()

      expect(testEdition.edition.instances[0].title).to.equal('inst2')
      expect(testEdition.edition.instances[1].title).to.equal('inst3')
      done()
    })
  })
})
