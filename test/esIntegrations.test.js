/* eslint-disable no-undef */
require('dotenv').config()
const request = require('supertest')
const chai = require('chai')
const sinonChai = require('sinon-chai')
const nock = require('nock')

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
      .post('/sfr/_search')
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
      v2Mock.post('/sfr_test/_search')
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
      v2Mock.post('/sfr_test/_search')
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

  describe('Utility Endpoints', () => {
    it('should respond with a list of languages for utils/languages', async () => {
      const langMock = nock(process.env.ELASTICSEARCH_HOST)
        .post('/sfr_test/_search')
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
      req.get('/v2/sfr/utils/languages')
        .then((resp) => {
          expect(resp.body.status).to.equal(200)
          expect(resp.body.data.languages[1].language).to.equal('Test2')
          // eslint-disable-next-line no-unused-expressions
          expect(langMock.isDone()).to.be.true
        })
    })

    it('should return list of languages with counts with total option on utils/languages', async () => {
      const langMock = nock(process.env.ELASTICSEARCH_HOST)
        .post('/sfr_test/_search')
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
      req.get('/v2/sfr/utils/languages?total=true')
        .then((resp) => {
          expect(resp.body.status).to.equal(200)
          expect(resp.body.data.languages[2].language).to.equal('Test3')
          expect(resp.body.data.languages[2].count).to.equal(2)
          // eslint-disable-next-line no-unused-expressions
          expect(langMock.isDone()).to.be.true
        })
    })
  })
})
