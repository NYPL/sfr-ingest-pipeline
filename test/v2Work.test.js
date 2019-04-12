/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const chaiPromise = require('chai-as-promised')

chai.should()
chai.use(sinonChai)
chai.use(chaiPromise)
const { expect } = chai

const { fetchWork } = require('../routes/v2/work')
const { ElasticSearchError, MissingParamError } = require('../lib/errors')

describe('v2 single work retrieval tests', () => {
  it('should raise an error if identifier is missing', (done) => {
    const params = {
      field: 'testing',
    }
    expect(fetchWork.bind(fetchWork, params, 'app')).to.throw(MissingParamError('Your request must include an identifier field or parameter'))
    done()
  })

  it('should return a single record for a successful query', async () => {
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
            _source: {
              uuid: 1,
              title: 'Test Work',
            },
          },
        ],
      },
    })
    const testApp = {
      client: {
        search: testClient,
      },
    }
    const params = {
      identifier: 1,
    }
    const resp = await fetchWork(params, testApp)
    expect(resp.uuid).to.equal(1)
    expect(resp.title).to.equal('Test Work')
  })

  it('should raise error if multiple records received', async () => {
    const testClient = sinon.stub()
    testClient.resolves({
      took: 0,
      timed_out: false,
      hits: {
        total: 1,
        max_score: 1,
        hits: [
          'hit1',
          'hit2',
        ],
      },
    })
    const testApp = {
      client: {
        search: testClient,
      },
    }
    const params = {
      identifier: 1,
    }
    const outcome = fetchWork(params, testApp)
    expect(outcome).to.eventually.throw(ElasticSearchError('Returned multiple records, identifier lacks specificity'))
  })
})
