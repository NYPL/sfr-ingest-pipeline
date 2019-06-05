/* eslint-disable no-undef */
require('dotenv').config()
const request = require('supertest')
const chai = require('chai')
const sinonChai = require('sinon-chai')

chai.should()
chai.use(sinonChai)
const { expect } = chai

describe('Testing Swagger Documentation', () => {
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

  it('test Swagger docs for well formed-ness', async () => {
    req.get('/research-now/swagger-test')
      .expect(200)
      .then((resp) => {
        expect(resp.text).to.equal('API name: ResearchNow Search API, Version: v0.2.3')
      })
  })

  it('should return all paths in swagger docs', async () => {
    req.get('/research-now/swagger')
      .expect(200)
      .then((resp) => {
        const apiPaths = []
        Object.keys(resp.body.paths).map(path => apiPaths.push(path))
        expect(apiPaths.length).to.equal(5)
      })
  })
})
