const request = require('supertest')
const chai = require('chai')
const sinonChai = require('sinon-chai')
chai.should()
chai.use(sinonChai)
const expect = chai.expect

describe('Testing ElasticSearch Integration', () => {
  let server
  beforeEach(() => {
    server = require('../app.js')
  })
  afterEach(() => {
    server.close()
  })

  it('responds to v2 search', (done) => {
    request(server)
      .get('/v2/sfr/search?field=keyword&query=the')
      .then(resp => {
        expect(resp.body.hits.total).to.be.greaterThan(0)
        done()
      })
  })

  it('response to v1 search', (done) => {
    request(server)
      .post('/api/v0.1/sfr/works')
      .send({
        queries: [{
          field: 'keyword',
          value: 'war'
        }]
      })
      .then(resp => {
        expect(resp.body.hits.total).to.be.greaterThan(0)
        done()
      })
  })
})
