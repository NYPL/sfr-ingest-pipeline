/* eslint-disable no-undef */
require('dotenv').config()
const request = require('supertest')
const chai = require('chai')
const sinonChai = require('sinon-chai')
const nock = require('nock')
const mockDB = require('mock-knex')

chai.should()
chai.use(sinonChai)
const { expect } = chai

describe('Testing ElasticSearch Integration', () => {
  let server
  let req
  beforeEach(() => {
    // eslint-disable-next-line global-require
    server = require('../app.js')
    req = request(server)
  })
  afterEach(() => {
    server.close()
  })

  it('response to v1 search', async () => {
    const v1Mock = nock(process.env.ELASTICSEARCH_HOST)
      .post(`/${process.env.ELASTICSEARCH_INDEX}/_search`)
      .reply(200, {
        took: 0,
        timed_out: false,
        hits: {
          total: 1,
          max_score: 1,
          hits: [
            {
              _index: 'sfr_test',
              _type: 'test',
              _id: 11,
              _score: 1,
            },
          ],
        },
        aggregations: {},
      })
    req.post('/api/v0.1/sfr/works')
      .send({
        queries: [{
          field: 'keyword',
          value: 'war',
        }],
      })
      .then((resp) => {
        expect(resp.body.hits.total).to.be.greaterThan(0)
        // eslint-disable-next-line no-underscore-dangle
        expect(resp.body.hits.hits[0]._id).to.equal(11)
        // eslint-disable-next-line no-unused-expressions
        expect(v1Mock.isDone()).to.be.true
      })
  })

  describe('v2 Search', () => {
    let v2Mock
    beforeEach(() => {
      v2Mock = nock(process.env.ELASTICSEARCH_HOST).post('/_count').reply(200, { count: 1 })
    })

    afterEach(() => {
      // Do Nothing
    })

    it('responds to v2 search', async () => {
      v2Mock.post(`/${process.env.ELASTICSEARCH_INDEX_V2}/_search`)
        .reply(200, {
          took: 0,
          timed_out: false,
          hits: {
            total: 1,
            max_score: 1,
            hits: [
              {
                _index: 'sfr_test',
                _type: 'test',
                _id: 31,
                _score: 1,
                _source: {
                  instances: [],
                },
              },
            ],
          },
          aggregations: {},
        })

      req.get('/v2/sfr/search?field=keyword&query=the')
        .then((resp) => {
          expect(resp.body.hits.total).to.be.greaterThan(0)
          // eslint-disable-next-line no-underscore-dangle
          expect(resp.body.hits.hits[0]._id).to.equal(31)
          // eslint-disable-next-line no-unused-expressions
          expect(v2Mock.isDone()).to.be.true
        })
    })

    it('sorts response by author', async () => {
      v2Mock.post(`/${process.env.ELASTICSEARCH_INDEX_V2}/_search`)
        .reply(200, {
          took: 0,
          timed_out: false,
          hits: {
            total: 2,
            max_score: 1,
            hits: [
              {
                _index: 'sfr_test',
                _type: 'test',
                _id: 32,
                _score: 1,
                _source: {
                  instances: [],
                  agents: [
                    {
                      name: 'Other Tester, Test',
                      sort_name: 'other tester, test',
                      roles: ['editor'],
                    },
                  ],
                },
              }, {
                _index: 'sfr_test',
                _type: 'test',
                _id: 31,
                _score: 1,
                _source: {
                  instances: [],
                  agents: [
                    {
                      name: 'Tester, Test',
                      sort_name: 'tester, test',
                      roles: ['author'],
                    },
                  ],
                },
              },
            ],
          },
          aggregations: {},
        })

      req.post('/v2/sfr/search')
        .send({
          query: 'the',
          field: 'keyword',
          sort: [
            {
              field: 'author',
            },
          ],
        })
        .then((resp) => {
          expect(resp.body.hits.total).to.be.greaterThan(0)
          // eslint-disable-next-line no-underscore-dangle
          expect(resp.body.hits.hits[0]._id).to.equal(32)
          // eslint-disable-next-line no-unused-expressions
          expect(v2Mock.isDone()).to.be.true
        })
    })
  })

  describe('v3 API search/work Endpoints', () => {
    const dbTracker = mockDB.getTracker()
    describe('v3 Search integration', () => {
      let v3Mock
      beforeEach(() => {
        v3Mock = nock(process.env.ELASTICSEARCH_HOST).post('/_count').reply(200, { count: 1 })
        dbTracker.install()
      })

      afterEach(() => {
        dbTracker.uninstall()
      })
      it('should respond with standard response object on success', async () => {
        v3Mock.post(`/${process.env.ELASTICSEARCH_INDEX_V3}/_search`)
          .reply(200, {
            took: 0,
            timed_out: false,
            hits: {
              total: 1,
              max_score: 1,
              hits: [
                {
                  _index: 'sfr_test',
                  _type: 'test',
                  _id: 32,
                  _score: 1,
                  _source: {
                    instances: [],
                    agents: [
                      {
                        name: 'Other Tester, Test',
                        sort_name: 'other tester, test',
                        roles: ['editor'],
                      },
                    ],
                  },
                  sort: [
                    'sort1',
                    'sort2',
                  ],
                },
              ],
            },
            aggregations: {},
          })

        dbTracker.on('query', (query, step) => {
          [
            () => {
              expect(query.sql).to.contain('from "works" where "uuid"')
              query.response({
                id: 1,
                title: 'tester',
              })
            },
            () => {
              expect(query.sql).to.contain('from "editions" where 1')
              query.response([
                {
                  id: 4,
                  pub_place: 'Testtown',
                  items: [],
                  publication_date: '[2020-01-01,2021-01-01)',
                },
              ])
            },
          ][step - 1]()
        })

        await req.post('/v3/sfr/search')
          .send({
            query: 'the',
            field: 'keyword',
            recordType: 'editions',
          })
          .then((resp) => {
            expect(resp.body.status).to.equal(200)
            expect(resp.body.data.totalWorks).to.equal(1)
            expect(resp.body.data.works[0].id).to.equal(1)
            expect(resp.body.responseType).to.equal('searchResults')
          })

        // eslint-disable-next-line no-unused-expressions
        expect(v3Mock.isDone()).to.be.true
      })

      it('should respond with standard error message if ElasticSearch errors', async () => {
        v3Mock.post(`/${process.env.ELASTICSEARCH_INDEX_V3}/_search`)
          .reply(400, {
            name: 'ElasticError',
            response: {
              error: {
                failed_shards: [
                  {
                    reason: {
                      caused_by: {
                        reason: 'Generic ElasticSearch Error',
                        type: 'testingError',
                      },
                    },
                  },
                ],
              },
            },
          })

        await req.post('/v3/sfr/search')
          .send({
            query: 'the',
            field: 'keyword',
            recordType: 'editions',
          })
          .then((resp) => {
            expect(resp.body.status).to.equal(500)
            expect(resp.body.name).to.equal('BadRequest')
            expect(resp.body.type).to.equal('testingError')
            expect(resp.body.reason).to.equal('Generic ElasticSearch Error')
          })

        // eslint-disable-next-line no-unused-expressions
        expect(v3Mock.isDone()).to.be.true
      })

      it('should respond with error if query is missing', async () => {
        await req.post('/v3/sfr/search')
          .send({
            field: 'keyword',
            recordType: 'editions',
          })
          .then((resp) => {
            expect(resp.body.status).to.equal(500)
            expect(resp.body.name).to.equal('MissingParamError')
            expect(resp.body.error).to.equal('Your request must include either a query object or an array of queries')
          })
      })
    })

    describe('v3 Work Integration', () => {
      const v3Work = nock(process.env.ELASTICSEARCH_HOST)
      beforeEach(() => {
        dbTracker.install()
      })

      afterEach(() => {
        dbTracker.uninstall()
      })
      it('should return a single work record on success', async () => {
        v3Work.post(`/${process.env.ELASTICSEARCH_INDEX_V3}/_search`)
          .reply(200, {
            took: 0,
            timed_out: false,
            hits: {
              total: 1,
              max_score: 1,
              hits: [
                {
                  _index: 'sfr_test',
                  _type: 'test',
                  _id: 32,
                  _score: 1,
                  _source: {
                    title: 'Found Work',
                    instances: [],
                    agents: [
                      {
                        name: 'Other Tester, Test',
                        sort_name: 'other tester, test',
                        roles: ['editor'],
                      },
                    ],
                  },
                  sort: [
                    'sort1',
                    'sort2',
                  ],
                },
              ],
            },
            aggregations: {},
          })

        dbTracker.on('query', (query, step) => {
          [
            () => {
              expect(query.sql).to.contain('from "works" where "uuid"')
              query.response({
                id: 1,
                title: 'Found Work',
              })
            },
            () => {
              expect(query.sql).to.contain('work_identifiers')
              query.response([
                {
                  ids: [5, 6],
                  type: 'test',
                },
              ])
            },
            () => {
              expect(query.sql).to.contain('test')
              query.response([
                {
                  value: 'id1',
                }, {
                  value: 'id2',
                },
              ])
            },
            () => {
              expect(query.sql).to.contain('editions')
              query.response([
                {
                  id: 4,
                  pub_place: 'Testtown',
                  items: [],
                  publication_date: '[2019-01-01,2020-01-01)',
                },
              ])
            },
          ][step - 1]()
        })

        await req.post('/v3/sfr/work')
          .send({ identifier: 'testIdentifier' })
          .then((resp) => {
            expect(resp.body.status).to.equal(200)
            expect(resp.body.data.id).to.equal(1)
            expect(resp.body.data.title).to.equal('Found Work')
            expect(resp.body.responseType).to.equal('workRecord')
          })

        // eslint-disable-next-line no-unused-expressions
        expect(v3Work.isDone()).to.be.true
      })

      it('should return an error if multiple works are found', async () => {
        v3Work.post(`/${process.env.ELASTICSEARCH_INDEX_V3}/_search`)
          .reply(200, {
            took: 0,
            timed_out: false,
            hits: {
              total: 1,
              max_score: 1,
              hits: [
                {
                  _index: 'sfr_test',
                  _type: 'test',
                  _id: 32,
                  _score: 1,
                  _source: {},
                },
                {
                  _index: 'sfr_test',
                  _type: 'test',
                  _id: 56,
                  _score: 1,
                  _source: {},
                },
              ],
            },
            aggregations: {},
          })

        await req.post('/v3/sfr/work')
          .send({ identifier: 'multiTest' })
          .then((resp) => {
            expect(resp.body.status).to.equal(500)
            expect(resp.body.name).to.equal('ElasticSearchError')
            expect(resp.body.error).to.equal('Returned multiple records, identifier lacks specificity')
          })

        // eslint-disable-next-line no-unused-expressions
        expect(v3Work.isDone()).to.be.true
      })
    })
  })

  describe('Utility Endpoints', () => {
    it('should respond with a list of languages for utils/languages', async () => {
      const langMock = nock(process.env.ELASTICSEARCH_HOST)
        .post(`/${process.env.ELASTICSEARCH_INDEX_V2}/_search`)
        .reply(200, {
          took: 0,
          timed_out: false,
          hits: {
            total: 2,
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
                  }, {
                    key: 'Test2',
                  }, {
                    key: 'Test3',
                  },
                ],
              },
            },
          },
        })
      await req.get('/v2/sfr/utils/languages')
        .then((resp) => {
          expect(resp.body.status).to.equal(200)
          expect(resp.body.data.languages[1].language).to.equal('Test2')
          // eslint-disable-next-line no-unused-expressions
          expect(langMock.isDone()).to.be.true
        })
    })

    it('should return list of languages with counts with total option on utils/languages', async () => {
      const langMock = nock(process.env.ELASTICSEARCH_HOST)
        .post(`/${process.env.ELASTICSEARCH_INDEX_V2}/_search`)
        .reply(200, {
          took: 0,
          timed_out: false,
          hits: {
            total: 2,
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
        })
      await req.get('/v2/sfr/utils/languages?total=true')
        .then((resp) => {
          expect(resp.body.status).to.equal(200)
          expect(resp.body.data.languages[2].language).to.equal('Test3')
          expect(resp.body.data.languages[2].count).to.equal(2)
          // eslint-disable-next-line no-unused-expressions
          expect(langMock.isDone()).to.be.true
        })
    })

    it('should return an object of document counts on utils/totals', async () => {
      const totalMock = nock(process.env.ELASTICSEARCH_HOST)
        .post(`/${process.env.ELASTICSEARCH_INDEX_V2}/_search`)
        .reply(200, {
          took: 0,
          timed_out: false,
          hits: {
            total: 2,
            max_score: 0,
            hits: [],
          },
          aggregations: {
            instances_inner: {
              doc_count: 10,
            },
            items_inner: {
              doc_count: 20,
            },
          },
        })
      await req.get('/v2/sfr/utils/totals?instances=true&items=true')
        .then((resp) => {
          expect(resp.body.status).to.equal(200)
          expect(resp.body.data.counts.works).to.equal(2)
          expect(resp.body.data.counts.instances).to.equal(10)
          expect(resp.body.data.counts.items).to.equal(20)
          // eslint-disable-next-line no-unused-expressions
          expect(totalMock.isDone()).to.be.true
        })
    })
  })
})
