const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const { mockRes } = require('sinon-express-mock')
chai.should()
chai.use(sinonChai)
const expect = chai.expect

const { respond, handleError } = require('../routes/v2/v2')

describe('Testing core v2 API Handler', () => {
  it('should return true for respond()', (done) => {
    const resp = {
      test: 'test'
    }
    const params = sinon.stub()
    const res = mockRes()
    const output = respond(res, resp, params)
    expect(output).to.be.true // eslint-disable-line
    expect(res.status).to.be.calledWith(200)
    done()
  })

  it('should return false for handleError()', (done) => {
    const err = {
      name: 'GenericError',
      message: 'A Test Error'
    }
    const res = mockRes()
    const output = handleError(res, err)
    expect(output).to.equal(false)
    expect(res.status).to.be.calledWith(500)
    done()
  })

  it('should return 404 for NotFound in handleError()', (done) => {
    const err = {
      name: 'NotFoundError',
      message: 'A Test Error'
    }
    const res = mockRes()
    const output = handleError(res, err)
    expect(output).to.equal(false)
    expect(res.status).to.be.calledWith(404)
    done()
  })
})
