/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const bodybuilder = require('bodybuilder')
const logger = require('../lib/logger')

chai.should()
chai.use(sinonChai)
const { expect } = chai

const Helpers = require('../helpers/esSourceHelpers')
const { V3Search } = require('../lib/v3Search')
const { MissingParamError, InvalidFilterError } = require('../lib/errors')

describe('v3 simple search tests', () => {
  describe('buildSearch()', () => {
    let stubBuildQuery
    let stubFilters
    let stubSort
    let stubAggs

    beforeEach(() => {
      stubBuildQuery = sinon.stub(V3Search.prototype, 'buildQuery')
      stubFilters = sinon.stub(V3Search.prototype, 'addFilters')
      stubSort = sinon.stub(V3Search.prototype, 'addSort')
      stubAggs = sinon.stub(V3Search.prototype, 'addAggregations')
    })

    afterEach(() => {
      stubBuildQuery.restore()
      stubFilters.restore()
      stubSort.restore()
      stubAggs.restore()
    })

    it('should raise an error if field or query is missing in build', (done) => {
      const testApp = sinon.stub()
      const params = {
        field: 'testing',
      }
      const testSearch = new V3Search(testApp, params)
      expect(testSearch.buildSearch.bind()).to.throw(MissingParamError('Your POST request must include either queries or filters'))
      done()
    })

    it('should create a query object with aggregations, filters and paging', (done) => {
      const testApp = sinon.stub()
      const testParams = {
        queries: [
          {
            field: 'keyword',
            query: 'testing',
          }, {
            field: 'subject',
            query: 'local',
          },
        ],
      }

      const testSearch = new V3Search(testApp, testParams)
      testSearch.buildSearch()
      /* eslint-disable no-unused-expressions */
      expect(stubBuildQuery.getCall(0).calledWith('keyword', 'testing')).to.be.true
      expect(stubBuildQuery.getCall(1).calledWith('subject', 'local')).to.be.true
      expect(stubFilters).to.have.been.calledOnce
      expect(stubSort).to.have.been.calledOnce
      expect(stubAggs).to.have.been.calledOnce
      /* eslint-enable no-unused-expressions */

      done()
    })

    it('should also accept a single search object', (done) => {
      const testApp = sinon.stub()
      const testParams = {
        field: 'keyword',
        query: 'testing',
      }

      const testSearch = new V3Search(testApp, testParams)
      testSearch.buildSearch()
      /* eslint-disable no-unused-expressions */
      expect(stubBuildQuery).to.have.been.calledOnceWith('keyword', 'testing')
      expect(stubFilters).to.have.been.calledOnce
      expect(stubSort).to.have.been.calledOnce
      expect(stubAggs).to.have.been.calledOnce
      /* eslint-enable no-unused-expressions */

      done()
    })
  })

  describe('buildQuery()', () => {
    let testApp = null
    let testParams = null
    let testSearch = null

    beforeEach(() => {
      testApp = sinon.stub()
      testParams = {}
      testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
    })

    afterEach(() => {})

    it('should raise error if field or query is missing from args', (done) => {
      expect(testSearch.buildQuery.bind('test')).to.throw(MissingParamError('Each query object in your request must contain query and field fields'))

      done()
    })

    it('should add a OR boolean query for author fields', (done) => {
      testSearch.buildQuery('author', 'Testing')

      const testQuery = testSearch.query.build()
      expect(testQuery.query.bool.should[0].nested.query.bool.must.query_string.query).to.equal('Testing')
      done()
    })

    it('should add a OR boolean query for viaf/lcnaf fields', (done) => {
      testSearch.buildQuery('viaf', 't0000000000')

      const testQuery = testSearch.query.build()
      expect(testQuery.query.bool.should[0].nested.query.term['agents.viaf']).to.equal('t0000000000')
      done()
    })

    it('should add a single nested query for subject searches', (done) => {
      testSearch.buildQuery('subject', 'testSubject')
      const testQuery = testSearch.query.build()
      expect(testQuery.query.nested.query.query_string.query).to.equal('testSubject')
      done()
    })

    it('should add a simple query for title searches', (done) => {
      testSearch.buildQuery('title', 'testTitle')
      const testQuery = testSearch.query.build()
      expect(testQuery.query.query_string.query).to.equal('testTitle')
      done()
    })

    it('should add a OR boolean query for keyword searches', (done) => {
      testSearch.buildQuery('keyword', 'testing')

      const testQuery = testSearch.query.build()
      expect(testQuery.query.bool.should[0].query_string.query).to.equal('testing')
      expect(testQuery.query.bool.should[1].nested.query.query_string.query).to.equal('testing')
      done()
    })
  })

  it('should query for a simple search field/query pair', async () => {
    const testClient = sinon.stub()
    testClient.resolves({
      took: 0,
      timed_out: false,
      hits: {
        total: 1,
        max_score: 1,
        hits: [
          {
            _index: 'sfr_test',
            _type: 'test',
            _id: 1,
            _score: 1,
          },
        ],
      },
      aggregations: {},
    })
    const testApp = {
      client: {
        search: testClient,
      },
    }
    const params = {
      field: 'test',
      query: 'testing',
    }
    const testSearch = new V3Search(testApp, params)
    testSearch.query = {
      build: sinon.stub(),
    }
    const loadStub = sinon.stub(V3Search.prototype, 'loadWorks')
    const instanceFilter = sinon.stub(V3Search, 'getInstanceOrEditions')
    const editionRangeStub = sinon.stub(V3Search, 'formatResponse').returns(1)
    const resp = await testSearch.execSearch()
    expect(resp).to.equal(1)
    editionRangeStub.restore()
    instanceFilter.restore()
    loadStub.restore()
  })

  it('should create facet object for response', (done) => {
    const testResp = {
      aggregations: {
        test_1: {
          test_2: {
            buckets: [
              {
                key: 'test1',
                test_3: { doc_count: 9 },
              },
              {
                key: 'test2',
                test_3: { doc_count: 3 },
              },
              {
                key: 'test3',
                test_3: { doc_count: 6 },
              },
            ],
          },
        },
      },
    }

    V3Search.formatResponseFacets(testResp)
    expect(testResp.facets.test.length).to.equal(3)
    expect(testResp.facets.test[1].value, 'test3')
    done()
  })

  it('should add aggregations for queries', (done) => {
    const testApp = sinon.mock()
    const testSearch = new V3Search(testApp, {})
    testSearch.query = bodybuilder()
    testSearch.addAggregations()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('aggs')
    expect(testBody.aggs).to.have.property('language_1')
    expect(testBody.aggs.language_1).to.have.property('nested')
    done()
  })

  describe('addFilters()', () => {
    it('should add gte/lte date filter on publication dates', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'years', value: { start: 1900, end: 2000 } }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testBody).to.have.property('query')
      expect(testBody.query.nested.query.bool.must[0].range['instances.pub_date'].gte.getTime()).to.equal(new Date('1900-01-01T00:00:00.000+00:00').getTime())
      expect(testBody.query.nested.query.bool.must[0].range['instances.pub_date'].lte.getTime()).to.equal(new Date('2000-12-31T24:00:00.000+00:00').getTime())
      done()
    })

    it('should add gte date filter on publication dates if only start is provided', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'years', value: { start: 1900 } }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testBody).to.have.property('query')
      expect(testBody.query.nested.query.bool.must[0].range['instances.pub_date'].gte.getTime()).to.equal(new Date('1900-01-01T00:00:00.000+00:00').getTime())
      // eslint-disable-next-line no-unused-expressions
      expect(testBody.query.nested.query.bool.must[0].range['instances.pub_date'].lte).to.be.undefined
      done()
    })

    it('should add multiple language filters in a bool query block', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'language', value: 'Testing' }, { field: 'language', value: 'Hello' }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testBody).to.have.property('query')
      expect(testBody.query.bool.must[0].nested.query.bool.must[1].nested.query.term['instances.languages.language']).to.equal('Testing')
      expect(testBody.query.bool.must[1].nested.query.bool.must[1].nested.query.term['instances.languages.language']).to.equal('Hello')
      done()
    })

    it('should add the show_all filter unless specific disabled', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = {}
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testBody).to.have.property('query')
      expect(testBody.query.nested.query.exists.field).to.equal('instances.formats')
      done()
    })

    it('should not include the show_all filter if disabled', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'show_all', value: true }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testBody).to.not.have.property('query')
      done()
    })

    it('should create an array of format filter options', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'format', value: 'pdf' }, { field: 'format', value: 'epub' }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      testSearch.addFilters()
      testBody = testSearch.query.build()
      expect(testSearch.formats).to.deep.equal(['application/pdf', 'application/epub+zip'])
      expect(testBody.query.nested.query.bool.must[1].terms).to.have.property('instances.formats')
      done()
    })

    it('should throw an InvalidFilterError if format is not recognized', (done) => {
      const testApp = sinon.mock()
      testApp.logger = logger
      const testParams = { filters: [{ field: 'format', value: 'pbf' }, { field: 'format', value: 'epub' }] }
      const testSearch = new V3Search(testApp, testParams)
      testSearch.query = bodybuilder()
      expect(testSearch.addFilters.bind()).to.throw(InvalidFilterError('Format filter value (pbf) must be one of the following: pdf, epub or html'))
      done()
    })
  })

  it('should sort on sort_title for a title sort option', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'title' }] }
    const testSearch = new V3Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('sort_title')
    expect(testBody.sort[0].sort_title.order).to.equal('ASC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should sort on agents.sort_name for an author sort', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'author', dir: 'DESC' }] }
    const testSearch = new V3Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('agents.sort_name')
    expect(testBody.sort[0]['agents.sort_name'].order).to.equal('DESC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should sort on instances.pub_date_sort for ASC date sort', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'date' }] }
    const testSearch = new V3Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('instances.pub_date_sort')
    expect(testBody.sort[0]['instances.pub_date_sort'].order).to.equal('ASC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should sort on instances.pub_date_sort_desc for DESC date sort', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'date', dir: 'DESC' }] }
    const testSearch = new V3Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('instances.pub_date_sort_desc')
    expect(testBody.sort[0]['instances.pub_date_sort_desc'].order).to.equal('DESC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should add a field sort for an arbitrary sort option', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'testing', dir: 'DESC' }] }
    const testSearch = new V3Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('testing')
    expect(testBody.sort[0].testing.order).to.equal('DESC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('sort should default to _score and uuid', (done) => {
    const testApp = sinon.mock()
    const testSearch = new V3Search(testApp, {})
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('_score')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  describe('formatResponse()', () => {
    it('should return a formatted data object', (done) => {
      const testWorks = 'works'
      const testResp = {
        hits: {
          total: 3,
        },
        paging: 'paging',
        facets: 'facets',
      }
      const formattedObj = V3Search.formatResponse(testWorks, testResp)
      expect(formattedObj.totalWorks).to.equal(3)
      expect(formattedObj.works).to.equal('works')
      done()
    })
  })

  describe('loadWorks()', () => {
    let testSearch
    let mockGet
    let mockGetInner
    beforeEach(() => {
      testSearch = new V3Search(sinon.mock(), {})
      mockGet = sinon.stub(V3Search.prototype, 'getWork')
      mockGetInner = sinon.stub(V3Search.prototype, 'getInnerRecords')
    })

    afterEach(() => {
      mockGet.restore()
      mockGetInner.restore()
    })

    it('should return an array of works with editions by default', async () => {
      const testWork1 = {
        uuid: 'testUUID1',
        edition_range: '2015-2019',
        sort: [1, 2],
      }
      const testWork2 = {
        uuid: 'testUUID2',
        edition_range: '1900-1905',
        sort: [3, 4],
      }
      const testWorks = [testWork1, testWork2]
      mockGet.onCall(0).returns({})
      mockGet.onCall(1).returns({})
      outWorks = await testSearch.loadWorks(testWorks)
      expect(outWorks.length).to.equal(2)
      expect(outWorks[1].edition_range).to.equal('1900-1905')
      /* eslint-disable no-unused-expressions */
      expect(mockGet).to.be.calledTwice
      expect(mockGetInner.getCall(0)).to.be.calledWith(
        testWork1,
        {
          instances: null,
          editions: null,
          edition_count: 0,
          edition_range: '2015-2019',
          sort: [1, 2],
        },
        'editions',
      )
      /* eslint-enable no-unused-expressions */
    })

    it('should return an array of works with instances if set', async () => {
      const testWork1 = {
        uuid: 'testUUID1',
        edition_range: '2015-2019',
        sort: [1, 2],
      }
      const testWorks = [testWork1]
      mockGet.onCall(0).returns({})
      outWorks = await testSearch.loadWorks(testWorks, 'instances')
      expect(outWorks.length).to.equal(1)
      expect(outWorks[0].edition_range).to.equal('2015-2019')
      /* eslint-disable no-unused-expressions */
      expect(mockGet).to.be.calledOnce
      expect(mockGetInner.getCall(0)).to.be.calledWith(
        testWork1,
        {
          instances: null,
          editions: null,
          edition_count: 0,
          edition_range: '2015-2019',
          sort: [1, 2],
        },
        'instances',
      )
      /* eslint-enable no-unused-expressions */
    })
  })

  describe('getInnerRecords()', () => {
    let testSearch
    let mockParseAgents
    let mockParseLinks
    beforeEach(() => {
      testSearch = new V3Search(sinon.mock(), {})
      mockParseAgents = sinon.stub(Helpers, 'parseAgents')
      mockParseLinks = sinon.stub(Helpers, 'parseLinks')
    })

    afterEach(() => {
      mockParseAgents.restore()
      mockParseLinks.restore()
    })

    it('should call getEditions when innerType set to editions', async () => {
      const mockGetEds = sinon.stub(V3Search.prototype, 'getEditions')
      const testWork = {
        instanceIds: [
          {
            edition_id: 1,
          }, {
            edition_id: 2,
          }, {
            edition_id: 3,
          },
        ],
      }
      const testDBWork = {}
      await testSearch.getInnerRecords(testWork, testDBWork, 'editions')
      expect(mockGetEds).to.be.calledOnceWith([1, 2, 3])
      expect(testDBWork.edition_count).to.equal(3)
      mockGetEds.restore()
    })

    it('should call getInstances when innerType set to instances', async () => {
      const mockGetInsts = sinon.stub(V3Search.prototype, 'getInstances')
      const testWork = {
        instanceIds: [
          {
            instance_id: 1,
          }, {
            instance_id: 2,
          }, {
            instance_id: 3,
          },
        ],
      }
      const testDBWork = {}
      await testSearch.getInnerRecords(testWork, testDBWork, 'instances')
      expect(mockGetInsts).to.be.calledOnceWith([1, 2, 3])
      expect(testDBWork.edition_count).to.equal(3)
      mockGetInsts.restore()
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
        took: 0,
        timed_out: false,
        hits: {
          total: 1,
          max_score: 1,
          hits: [
            {
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
            },
          ],
        },
        aggregations: {},
      }

      const fetchObjects = V3Search.getInstanceOrEditions(testResp)
      // eslint-disable-next-line no-unused-expressions
      expect(mockFormatRange).to.be.calledOnce
      expect(fetchObjects[0].uuid).to.equal(1)
      expect(fetchObjects[0].instanceIds[0].instance_id).to.equal(10)
      expect(fetchObjects[0].instanceIds[1].edition_id).to.equal(42)
      done()
    })

    it('should remove any empty instance records', (done) => {
      const testResp = {
        took: 0,
        timed_out: false,
        hits: {
          total: 1,
          max_score: 1,
          hits: [
            {
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
            },
          ],
        },
        aggregations: {},
      }

      const fetchObjects = V3Search.getInstanceOrEditions(testResp)
      // eslint-disable-next-line no-unused-expressions
      expect(mockFormatRange).to.be.calledOnce
      expect(fetchObjects[0].uuid).to.equal(1)
      expect(fetchObjects[0].instanceIds.length).to.equal(3)
      expect(fetchObjects[0].instanceIds[0].instance_id).to.equal(102)
      expect(fetchObjects[0].instanceIds[1].edition_id).to.equal(11)
      done()
    })
  })

  describe('formatResponsePaging()', () => {
    it('should return formatted paging object in response', (done) => {
      const testResp = {
        hits: {
          hits: [
            {
              sort: 'startSort',
            }, {
              sort: 'middleSort',
            }, {
              sort: 'endSort',
            },
          ],
        },
      }

      V3Search.formatResponsePaging(testResp)
      expect(testResp.paging.prev_page_sort).to.equal('startSort')
      expect(testResp.paging.next_page_sort).to.equal('endSort')
      done()
    })
  })

  describe('getAggBottom()', () => {
    it('should recursively call itself to get root aggregation', (done) => {
      const testAgg = {
        test_1: {
          test_2: {
            test_3: {
              buckets: 'rootBuckets',
            },
          },
        },
      }
      const aggBottom = V3Search.getAggBottom(testAgg, 'test', 1)
      expect(aggBottom.buckets).to.equal('rootBuckets')
      expect(aggBottom.lastLevel).to.equal('test_4')
      done()
    })
  })

  describe('aggPaging()', () => {
    let testSearch
    let mockCount
    beforeEach(() => {
      const mockApp = sinon.mock()
      mockApp.logger = {
        info: sinon.mock(),
        debug: sinon.mock(),
      }
      testSearch = new V3Search(mockApp, {})
      testSearch.query = bodybuilder()
      mockCount = sinon.stub(V3Search.prototype, 'getQueryCount')
    })

    afterEach(() => {
      mockCount.restore()
    })

    it('should set standard sort option for random page before 10000 items', async () => {
      testSearch.params = {
        page: 104,
        perPage: 10,
      }
      await testSearch.addPaging()
      const testQuery = testSearch.query.build()
      expect(testQuery.size).to.equal(10)
      expect(testQuery.from).to.equal(1040)
    })

    it('should set search to next page if next_page_sort set', async () => {
      testSearch.params = {
        next_page_sort: 'nextPageParams',
      }
      await testSearch.addPaging()
      const testQuery = testSearch.query.build()
      expect(testQuery.size).to.equal(10)
      expect(testQuery.search_after).to.equal('nextPageParams')
    })

    it('should set search to previous page if prev_page_sort set', async () => {
      const mockInvert = sinon.stub(V3Search.prototype, 'invertSort')
      testSearch.params = {
        prev_page_sort: 'prevPageParams',
      }
      await testSearch.addPaging()
      const testQuery = testSearch.query.build()
      expect(testQuery.size).to.equal(10)
      expect(testQuery.search_after).to.equal('prevPageParams')
      // eslint-disable-next-line no-unused-expressions
      expect(mockInvert).to.be.calledOnce
      mockInvert.restore()
    })

    it('should set search from end of results for results close to end', async () => {
      const mockInvert = sinon.stub(V3Search.prototype, 'invertSort')
      testSearch.params = {
        total: 100000,
        page: 1990,
        per_page: 50,
      }
      await testSearch.addPaging()
      const testQuery = testSearch.query.build()
      expect(testQuery.size).to.equal(50)
      expect(testQuery.from).to.equal(500)
      /* eslint-disable no-unused-expressions */
      expect(testSearch.reverseResult).to.be.true
      expect(mockInvert).to.be.calledOnce
      /* eslint-enable no-unused-expressions */
      mockInvert.restore()
    })

    it('should perform recursive search for retrieval from middle of large set', async () => {
      const mockRecursive = sinon.stub(V3Search.prototype, 'recursiveSearch')
      mockRecursive.returns('deepSearchAfter')
      testSearch.params = {
        total: 100000,
        page: 1000,
        per_page: 50,
      }
      await testSearch.addPaging()
      const testQuery = testSearch.query.build()
      expect(testQuery.size).to.equal(50)
      expect(testQuery.from).to.equal(0)
      expect(testQuery.search_after).to.equal('deepSearchAfter')
      /* eslint-disable no-unused-expressions, no-underscore-dangle */
      expect(testQuery._source).to.be.true
      expect(mockRecursive).to.be.calledOnceWith(1000, 50000, 10000)
      /* eslint-enable no-unused-expressions */
      mockRecursive.restore()
    })
  })

  describe('recursiveSearch()', () => {
    let testSearch
    let mockExec
    beforeEach(() => {
      const mockApp = sinon.mock()
      mockApp.logger = {
        info: sinon.mock().atLeast(1),
        debug: sinon.mock().atLeast(1),
      }
      testSearch = new V3Search(mockApp, {})
      testSearch.query = bodybuilder()
      mockExec = sinon.stub(V3Search.prototype, 'execSearch')
    })

    afterEach(() => {
      mockExec.restore()
    })

    it('should not recurse if within 1,000 of result', async () => {
      mockExec.returns({
        hits: { hits: [{}, {}, { sort: 'returnedAfter' }] },
      })
      const testAfter = await testSearch.recursiveSearch(25, 11000, 11025, 'searchAfter')
      const testQuery = testSearch.query.build()
      expect(testQuery.from).to.equal(0)
      /* eslint-disable no-unused-expressions */
      expect(testQuery._source).to.be.false
      expect(testQuery.search_after).to.equal('searchAfter')
      expect(testQuery.size).to.equal(0)
      expect(testAfter).to.equal('returnedAfter')
      expect(mockExec).to.be.calledOnce
      /* eslint-enable no-unused-expressions */
    })

    it('should recurse without a searchAfter value', async () => {
      mockExec.returns({
        hits: { hits: [{}, {}, { sort: 'intReturn' }] },
      }).returns({
        hits: { hits: [{}, {}, { sort: 'finalReturn' }] },
      })
      const testAfter = await testSearch.recursiveSearch(1000, 11025, 11000)
      const testQuery = testSearch.query.build()
      /* eslint-disable no-unused-expressions */
      expect(testQuery._source).to.be.false
      expect(testAfter).to.equal('finalReturn')
      expect(mockExec).to.be.calledTwice
      /* eslint-enable no-unused-expressions */
    })
  })

  describe('invertSort()', () => {
    let testSearch
    beforeEach(() => {
      const mockApp = sinon.mock()
      mockApp.logger = {
        info: sinon.mock().atLeast(1),
        debug: sinon.mock().atLeast(1),
      }
      testSearch = new V3Search(mockApp, {})
      testSearch.query = bodybuilder()
    })

    afterEach(() => {
      // Nothing to do
    })
    it('should replace sort value with inverse in query', (done) => {
      testSearch.query.sort([
        { test1: 'asc' },
        { test2: 'desc' },
      ])
      testSearch.invertSort()
      testQuery = testSearch.query.build()
      expect(testQuery.sort[0].test1.order).to.equal('desc')
      expect(testQuery.sort[1].test2.order).to.equal('asc')
      done()
    })
  })
})
