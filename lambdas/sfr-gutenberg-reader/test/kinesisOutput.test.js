/* eslint-disable semi, no-undef, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinonChai from 'sinon-chai'
import nock from 'nock'
import Kinesis from '../src/kinesisOutput'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const { expect } = chai

describe('Kinesis Output [kinesisOutput.js]', () => {
  describe('exports.resultHandler()', () => {
    it('should return success message on kinesis success', async () => {
      nock('https://kinesis.us-east-1.amazonaws.com')
        .post('/')
        .reply(200, {
          EncryptionType: 'NONE',
          SequenceNumber: '0000001',
          ShardId: 'Shard-0000000000',
        })
      const mockData = {
        gutenbergID: '0000',
        data: {
          title: 'Hello',
          alt_titles: 'Test Data',
          entities: [],
          subjects: [],
        },
        status: 200,
        message: 'Retrieved Gutenberg Metadata',
      }
      const kinResp = await Kinesis.resultHandler(mockData)
      expect(kinResp.EncryptionType).to.equal('NONE')
      expect(kinResp.SequenceNumber).to.equal('0000001')
      expect(kinResp.ShardId).to.equal('Shard-0000000000')
    })

    it('should return failuer message if kinesis put fails', async () => {
      nock('https://kinesis.us-east-1.amazonaws.com')
        .post('/')
        .reply(404, { message: 'Kinesis Put Failed!' })
      const mockData = {
        gutenbergID: '0000',
        data: {
          title: 'Failure',
          alt_titles: 'Test Fail Data',
          entities: [],
          subjects: [],
        },
        status: 200,
        message: 'Retrieved Gutenberg Metadata'
      }
      const kinResp = await Kinesis.resultHandler(mockData)
      expect(kinResp.message).to.equal('Kinesis Put Failed!')
      expect(kinResp.statusCode).to.equal(404)
    })
  })
})
