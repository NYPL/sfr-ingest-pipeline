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

  it('responds to v2 search', async () => {
    const v2Mock = nock(process.env.ELASTICSEARCH_HOST)
      .post('/_count')
      .reply(200, { count: 1 })
      .post('/sfr_test/_search')
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
})
