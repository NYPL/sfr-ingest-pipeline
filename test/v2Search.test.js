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
const { Search } = require('../lib/search')
const { MissingParamError } = require('../lib/errors')

describe('v2 simple search tests', () => {
  it('should raise an error if field or query is missing in build', (done) => {
    const testApp = sinon.stub()
    const params = {
      field: 'testing',
    }
    const testSearch = new Search(testApp, params)
    expect(testSearch.buildSearch.bind()).to.throw(MissingParamError('Your POST request must include either queries or filters'))
    done()
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
    const testSearch = new Search(testApp, params)
    testSearch.query = {
      build: sinon.stub(),
    }
    const instanceFilter = sinon.stub(Search, 'filterSearchEditions')
    const editionRangeStub = sinon.stub(Helpers, 'formatResponseEditionRange')
    const resp = await testSearch.execSearch()
    expect(resp.took).to.equal(0)
    expect(resp.hits.hits.length).to.equal(1)
    editionRangeStub.restore()
    instanceFilter.restore()
  })

  it('should create facet object for response', (done) => {
    const testResp = {
      aggregations: {
        test: {
          test: {
            buckets: [
              {
                key: 'test1',
                test: { doc_count: 9 },
              },
              {
                key: 'test2',
                test: { doc_count: 3 },
              },
              {
                key: 'test3',
                test: { doc_count: 6 },
              },
            ],
          },
        },
      },
    }

    Search.formatResponseFacets(testResp)
    expect(testResp.facets.test.length).to.equal(3)
    expect(testResp.facets.test[1].value, 'test3')
    done()
  })

  it('should add aggregations for queries', (done) => {
    const testApp = sinon.mock()
    const testSearch = new Search(testApp, {})
    testSearch.query = bodybuilder()
    testSearch.addAggregations()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('aggs')
    expect(testBody.aggs).to.have.property('language')
    expect(testBody.aggs.language).to.have.property('nested')
    done()
  })

  it('should add gte/lte date filter on publication dates', (done) => {
    const testApp = sinon.mock()
    testApp.logger = logger
    const testParams = { filters: [{ field: 'years', value: { start: 1900, end: 2000 } }] }
    const testSearch = new Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addFilters()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('query')
    expect(testBody.query.nested.query.range['instances.pub_date'].gte.getTime()).to.equal(new Date('1900-01-01T12:00:00.000+00:00').getTime())
    expect(testBody.query.nested.query.range['instances.pub_date'].lte.getTime()).to.equal(new Date('2000-12-31T12:00:00.000+00:00').getTime())
    done()
  })

  it('should add gte date filter on publication dates if only start is provided', (done) => {
    const testApp = sinon.mock()
    testApp.logger = logger
    const testParams = { filters: [{ field: 'years', value: { start: 1900 } }] }
    const testSearch = new Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addFilters()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('query')
    expect(testBody.query.nested.query.range['instances.pub_date'].gte.getTime()).to.equal(new Date('1900-01-01T12:00:00.000+00:00').getTime())
    // eslint-disable-next-line no-unused-expressions
    expect(testBody.query.nested.query.range['instances.pub_date'].lte).to.be.undefined
    done()
  })

  it('should sort on sort_title for a title sort option', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'title' }] }
    const testSearch = new Search(testApp, testParams)
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('sort_title')
    expect(testBody.sort[0].sort_title.order).to.equal('ASC')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should add a field sort for an arbitrary sort option', (done) => {
    const testApp = sinon.mock()
    const testParams = { sort: [{ field: 'testing', dir: 'DESC' }] }
    const testSearch = new Search(testApp, testParams)
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
    const testSearch = new Search(testApp, {})
    testSearch.query = bodybuilder()
    testSearch.addSort()
    testBody = testSearch.query.build()
    expect(testBody).to.have.property('sort')
    expect(testBody.sort[0]).to.have.property('_score')
    expect(testBody.sort[1]).to.have.property('uuid')
    done()
  })

  it('should slice instance array down to first 3 instances', (done) => {
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
                { id: 1 },
                { id: 2 },
                { id: 3 },
                { id: 4 },
              ],
            },
          },
        ],
      },
      aggregations: {},
    }
    Search.filterSearchEditions(testResp)
    /* eslint-disable no-underscore-dangle */
    expect(testResp.hits.hits[0]._source.instances.length).to.equal(3)
    expect(testResp.hits.hits[0]._source.instances[2].id).to.equal(3)
    /* eslint-enable no-underscore-dangle */
    done()
  })
})
