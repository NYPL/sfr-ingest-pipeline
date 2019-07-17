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
      it('should call execQuery() with ES query', (done) => {
        const buildStub = sinon.stub(Utils, 'buildQuery')
        const execQuery = sinon.stub(Utils, 'execQuery')
        const bodyStub = sinon.fake()
        bodyStub.build = () => 'testBodyBuild'
        buildStub.returns(bodyStub)

        const checkQuery = {
          index: process.env.ELASTICSEARCH_INDEX_V2,
          body: 'testBodyBuild',
        }

        Utils.fetchLangs('app', { total: true })
        expect(buildStub).to.have.been.calledOnceWith(true)
        expect(execQuery).to.have.been.calledOnceWith('app', checkQuery, true)
        buildStub.restore()
        execQuery.restore()
        done()
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

    describe('execQuery()', () => {
      let parseStub = null
      beforeEach(() => {
        parseStub = sinon.stub(Utils, 'parseLanguageAgg')
      })

      afterEach(() => {
        parseStub.restore()
      })

      it('should return language array on successful query', async () => {
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
        parseStub.returns(testResp.aggregations.language_inner.unique_languages.buckets)

        const execResp = await Utils.execQuery(fakeApp, {}, true)
        expect(execResp).to.be.instanceOf(Array)
        expect(execResp[1].key).to.equal('Test2')
        expect(execResp[0].inner_count.doc_count).to.equal(5)
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
        const fakeApp = sinon.fake()
        const fakeClient = sinon.fake()
        const fakeSearch = sinon.fake.resolves(testResp)
        fakeClient.search = fakeSearch
        fakeApp.client = fakeClient
        const result = Utils.execQuery(fakeApp, {}, true)
        expect(result).to.eventually.throw(new ElasticSearchError('Could not load language aggregations'))
        // eslint-disable-next-line no-unused-expressions
        expect(parseStub).to.not.be.called
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
        // eslint-disable-next-line no-unused-expressions
        expect(parseStub).to.not.be.called
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

    describe('formatLanguageResponse()', () => {
      it('should return respone object containing array', (done) => {
        const testResp = Utils.formatLanguageResponse('testArray')
        expect(testResp.status).to.equal(200)
        expect(testResp.data.languages).to.equal('testArray')
        done()
      })
    })
  })
})
