/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const Helpers = require('../helpers/esSourceHelpers')


chai.should()
chai.use(sinonChai)
const { expect } = chai

describe('ElasticSearch Response Parser Helpers', () => {
  describe('getEditionRangeValue()', () => {
    let stubGetRange
    beforeEach(() => {
      stubGetRange = sinon.stub(Helpers, 'getEditionRangeValue')
      stubGetRange.onFirstCall().returns('1900')
      stubGetRange.onSecondCall().returns('2000')
    })

    afterEach(() => {
      stubGetRange.restore()
    })

    it('should return a year from an array of editions', (done) => {
      const testResp = {
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
              _source: {},
            },
          ],
        },
      }
      Helpers.formatResponseEditionRange(testResp)
      // eslint-disable-next-line no-underscore-dangle
      expect(testResp.hits.hits[0]._source.edition_range).to.equal('1900 - 2000')
      done()
    })
  })

  it('should get a year for a provided set of editions', (done) => {
    const stubCompare = sinon.stub(Helpers, 'startEndCompare')
    const testHit = {
      _source: {
        instances: [
          {
            pub_date: {
              gte: '2019-01-01',
              lte: '2020-12-31',
            },
          }, {
            pub_date: null,
          },
        ],
      },
    }

    const testStart = Helpers.getEditionRangeValue(testHit, 'gte', 1)
    const testEnd = Helpers.getEditionRangeValue(testHit, 'lte', -1)
    expect(testStart).to.equal(2019)
    expect(testEnd).to.equal(2020)
    stubCompare.restore()
    done()
  })

  it('should return ???? if no pub date found', (done) => {
    const stubCompare = sinon.stub(Helpers, 'startEndCompare')
    const testHit = {
      _source: {
        instances: [
          {
            pub_date: null,
          },
        ],
      },
    }

    const testStart = Helpers.getEditionRangeValue(testHit, 'gte', 1)
    const testEnd = Helpers.getEditionRangeValue(testHit, 'lte', -1)
    expect(testStart).to.equal('????')
    expect(testEnd).to.equal('????')
    stubCompare.restore()
    done()
  })

  it('should generate a comparison function for sorting', (done) => {
    const compareFunction = Helpers.startEndCompare('gte', 1)
    expect(compareFunction).to.be.instanceOf(Function)
    const edition1 = { pub_date: { gte: '1999-01-01', lte: null } }
    const edition2 = { pub_date: { gte: '2000-01-01', lte: null } }
    const order = compareFunction(edition1, edition2)
    expect(order).to.equal(-1)
    done()
  })
})
