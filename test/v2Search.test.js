const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
chai.should()
chai.use(sinonChai)
const expect = chai.expect

const { simpleSearch } = require('../routes/v2/search')
const { MissingParamError } = require('../lib/errors')

describe('v2 simple search tests', () => {
  it('should raise an error if field or query is missing', async (done) => {
    const params = {
      'field': 'testing'
    }
    expect(simpleSearch.bind(simpleSearch, params, 'app')).to.throw(MissingParamError('Your POST request must include either queries or filters'))
    done()
  })

  it('should query for a simple search field/query pair', async () => {
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
            _type: 'teest',
            _id: 1,
            _score: 1
          }
        ]
      }
    })
    const testApp = {
      client: {
        search: testClient
      }
    }
    const params = {
      field: 'test',
      query: 'testing'
    }
    const resp = await simpleSearch(params, testApp)
    expect(resp.took).to.equal(0)
    expect(resp.hits.hits.length).to.equal(1)
  })
})
