import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinonChai from 'sinon-chai'
import AWS from 'aws-sdk-mock'

import { setEnv } from '../src/env_config.js'
import { resultHandler } from '../src/kinesis_out.js'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

setEnv()

describe('Kinesis Output [kinesis_out.js]', () => {
  describe('resultHandler(reportData, metaBlock, status)', () => {
    it('should return a response for a successful report generation', async () => {
      AWS.mock('Kinesis', 'putRecord', 'response')
      const mockMeta = {
        instanceID: 1,
        identifier: 1
      }
      const resp = await resultHandler({}, mockMeta, 200)

      expect(resp).to.equal('response')
      AWS.restore('Kinesis')
    })

    it('should return a response for a failed report generation', async () => {
      AWS.mock('Kinesis', 'putRecord', 'response')
      const mockMeta = {
        instanceID: 1,
        identifier: 1
      }
      const resp = await resultHandler({}, mockMeta, 500)

      expect(resp).to.equal('response')
      AWS.restore('Kinesis')
    })

    it('should return an error object if Kinesis fails', async () => {
      AWS.mock('Kinesis', 'putRecord', () => {
        return new Promise((resolve, reject) => {
          reject(new Error('kinesis error'))
        })
      })
      const mockMeta = {
        instanceID: 1,
        identifier: 1
      }
      const resp = await resultHandler({}, mockMeta, 500)
      expect(resp.message).to.equal('kinesis error')
      AWS.restore('Kinesis')
    })
  })
})
