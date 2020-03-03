/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const chaiPromise = require('chai-as-promised')

chai.should()
chai.use(sinonChai)
chai.use(chaiPromise)
const { expect } = chai

const Utils = require('../routes/v2/utils')
const { ElasticSearchError } = require('../lib/errors')

describe('v2 utility endpoints', () => {
  describe('language list utility', () => {
    describe('fetchLangs()', () => {
      let buildStub
      let execQuery
      let parseStub
      let bodyStub

      beforeEach(() => {
        buildStub = sinon.stub(Utils, 'buildQuery')
        execQuery = sinon.stub(Utils, 'execQuery')
        parseStub = sinon.stub(Utils, 'parseLanguageAgg')
        bodyStub = sinon.fake()
        bodyStub.build = () => 'testBodyBuild'
        buildStub.returns(bodyStub)
      })

      afterEach(() => {
        buildStub.restore()
        execQuery.restore()
        parseStub.restore()
      })

      it('should call execQuery() with ES query', async () => {
        const testResp = {
          hits: {
            total: 0,
            max_score: 0,
            hits: [],
          },
          aggregations: {
            language_inner: {
              doc_count: 1,
              unique_language: {
                buckets: [],
              },
            },
          },
        }
        execQuery.returns(testResp)
        const checkQuery = {
          index: process.env.ELASTICSEARCH_INDEX_V2,
          body: 'testBodyBuild',
        }

        await Utils.fetchLangs('app', { total: true })
        expect(buildStub).to.have.been.calledOnceWith(true)
        expect(execQuery).to.have.been.calledOnceWith('app', checkQuery, true)
        // eslint-disable-next-line no-unused-expressions
        expect(parseStub).to.have.been.calledOnce
      })

      it('should raise ElasticSearchError if no docs are returned', async () => {
        const testResp = {
          hits: {
            total: 0,
            max_score: 0,
            hits: [],
          },
          aggregations: {
            language_inner: {
              doc_count: 0,
              unique_language: {
                buckets: [],
              },
            },
          },
        }
        execQuery.returns(testResp)
        const resp = Utils.fetchLangs('app', { total: true })
        expect(resp).to.eventually.be.rejectedWith(new ElasticSearchError('Could not load language aggregations'))
      })
    })

    describe('buildQuery()', () => {
      it('should build query with inner_count if total is true', (done) => {
        const testBody = Utils.buildQuery(true).build()
        expect(testBody.size).to.equal(0)
        expect(testBody.query).to.deep.equal({ match_all: {} })
        expect(testBody.aggs.language_inner.aggs.unique_languages.terms.field).to.equal('instances.language.language')
        expect(testBody.aggs.language_inner.aggs.unique_languages.terms.size).to.equal(250)
        const innerCount = testBody.aggs.language_inner.aggs.unique_languages.aggs.inner_count
        expect(innerCount).to.deep.equal({ reverse_nested: {} })
        done()
      })

      it('should build query without inner_count if total is false-y', (done) => {
        const testBody = Utils.buildQuery(false).build()
        expect(testBody.size).to.equal(0)
        expect(testBody.query).to.deep.equal({ match_all: {} })
        expect(testBody.aggs.language_inner.aggs.unique_languages.terms.field).to.equal('instances.language.language')
        expect(testBody.aggs.language_inner.aggs.unique_languages.terms.size).to.equal(250)
        // eslint-disable-next-line no-unused-expressions
        expect(testBody.aggs.language_inner.aggs.unique_languages.aggs).to.be.undefined
        done()
      })
    })

    describe('parseLanguageAgg()', () => {
      let testAggs = null
      beforeEach(() => {
        testAggs = {
          unique_languages: {
            buckets: [
              {
                key: 'Test1',
                inner_count: {
                  doc_count: 5,
                },
              }, {
                key: 'Test2',
                inner_count: {
                  doc_count: 3,
                },
              }, {
                key: 'Test3',
                inner_count: {
                  doc_count: 2,
                },
              },
            ],
          },
        }
      })

      afterEach(() => {})

      it('should return array of languages without totals it total is false', (done) => {
        const testArray = Utils.parseLanguageAgg(testAggs, false)
        expect(testArray[0]).to.deep.equal({ language: 'Test1' })
        expect(testArray[2]).to.deep.equal({ language: 'Test3' })
        done()
      })

      it('should return array of languages with totals it total is true', (done) => {
        const testArray = Utils.parseLanguageAgg(testAggs, true)
        expect(testArray[0]).to.deep.equal({ language: 'Test1', count: 5 })
        expect(testArray[2]).to.deep.equal({ language: 'Test3', count: 2 })
        done()
      })
    })
  })

  describe('Count fetch utility', () => {
    describe('fetchCounts()', () => {
      let bodyStub
      let execStub
      let parseStub

      beforeEach(() => {
        execStub = sinon.stub(Utils, 'execQuery')
        parseStub = sinon.stub(Utils, 'parseTotalCounts')
        bodyStub = sinon.fake()
        bodyStub.build = () => 'testBodyBuild'
      })

      afterEach(() => {
        execStub.restore()
        parseStub.restore()
      })

      it('should return parsed count object', async () => {
        execStub.returns('elasticResponse')
        parseStub.returns('totalCounts')
        const outObject = await Utils.fetchCounts('app', { instances: 'true' })
        // eslint-disable-next-line no-unused-expressions
        expect(execStub).to.be.calledOnce
        expect(parseStub).to.be.calledOnceWith('elasticResponse')
        expect(outObject).to.equal('totalCounts')
      })
    })

    describe('parseTotalCounts()', () => {
      it('should return only work total if no aggregations are made', (done) => {
        const testCounts = {
          hits: {
            total: 10,
          },
        }
        const parsedCounts = Utils.parseTotalCounts(testCounts)
        expect(parsedCounts.works).to.equal(10)
        expect(Object.keys(parsedCounts).length).to.equal(1)
        done()
      })

      it('should return additional counts if aggregations present', (done) => {
        const testCounts = {
          hits: {
            total: 10,
          },
          aggregations: {
            test_inner: {
              doc_count: 20,
            },
            test2_inner: {
              doc_count: 30,
            },
          },
        }
        const parsedCounts = Utils.parseTotalCounts(testCounts)
        expect(Object.keys(parsedCounts).length).to.equal(3)
        expect(parsedCounts.test2).to.equal(30)
        expect(parsedCounts.works).to.equal(10)
        done()
      })
    })
  })

  describe('shared utility methods', () => {
    describe('formatResponse()', () => {
      it('should return response object containing array', (done) => {
        const testResp = Utils.formatResponse({ languages: 'testArray' })
        expect(testResp.status).to.equal(200)
        expect(testResp.data.languages).to.equal('testArray')
        done()
      })
    })

    describe('execQuery()', () => {
      it('should return ElasticSearch response on successful query', async () => {
        const testResp = {
          hits: {
            total: 10,
            max_score: 0,
            hits: [],
          },
          aggregations: {
            language_inner: {
              doc_count: 10,
              unique_languages: {
                buckets: [
                  {
                    key: 'Test1',
                    inner_count: {
                      doc_count: 5,
                    },
                  }, {
                    key: 'Test2',
                    inner_count: {
                      doc_count: 3,
                    },
                  }, {
                    key: 'Test3',
                    inner_count: {
                      doc_count: 2,
                    },
                  },
                ],
              },
            },
          },
        }
        const fakeApp = sinon.fake()
        const fakeClient = sinon.fake()
        const fakeSearch = sinon.fake.resolves(testResp)
        fakeClient.search = fakeSearch
        fakeApp.client = fakeClient

        const execResp = await Utils.execQuery(fakeApp, {}, true)
        expect(execResp).to.be.instanceOf(Object)
        expect(execResp.hits.total).to.equal(10)
        expect(execResp.aggregations.language_inner.doc_count).to.equal(10)
      })

      it('should reject on a generic error', async () => {
        const testResp = {
          error: 'testError',
        }
        const fakeApp = sinon.fake()
        const fakeClient = sinon.fake()
        const fakeSearch = sinon.fake.rejects(testResp)
        fakeClient.search = fakeSearch
        fakeApp.client = fakeClient
        try {
          await Utils.execQuery(fakeApp, {}, true)
        } catch (err) {
          expect(err).to.be.instanceOf(Error)
        }
      })
    })
  })
})
