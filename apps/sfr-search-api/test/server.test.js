/* eslint-disable no-undef */
const request = require('supertest')
const chai = require('chai')
const sinonChai = require('sinon-chai')

chai.should()
chai.use(sinonChai)
const { expect } = chai

describe('Testing basic express setup', () => {
  let server
  beforeEach(() => {
    // eslint-disable-next-line global-require
    server = require('../app.js')
  })
  afterEach(() => {
    server.close()
  })

  it('responds to / with v1 test statement', (done) => {
    request(server)
      .get('/')
      .then((resp) => {
        expect(resp.body.apiVersion).to.equal('v1')
        done()
      })
  })

  it('response to /v2 with v2 test statement', (done) => {
    request(server)
      .get('/v2')
      .then((resp) => {
        expect(resp.body.apiVersion).to.equal('v2')
        done()
      })
  })

  it('response with swagger docs to /research-now/swagger', (done) => {
    request(server)
      .get('/research-now/swagger')
      .then((resp) => {
        expect(resp.body.swagger, '2.0')
        done()
      })
  })
})
