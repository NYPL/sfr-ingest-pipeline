import AWS from 'aws-sdk'
import logger from './helpers/logger'

AWS.config.update({
  region: 'us-east-1',
  logger: process.stdout,
})

let customKinEndpoint
if (process.env.AWS_KINESIS_ENDPOINT) {
  customKinEndpoint = {
    endpoint: process.env.AWS_KINESIS_ENDPOINT,
  }
}

const kinesis = new AWS.Kinesis(customKinEndpoint)

exports.resultHandler = (handleResp) => new Promise((resolve) => {
  const outParams = {
    Data: JSON.stringify(handleResp),
    PartitionKey: process.env.AWS_KINESIS_STREAMID,
    StreamName: process.env.AWS_KINESIS_STREAMNAME,
  }
  const kinesisOut = kinesis.putRecord(outParams).promise()
  kinesisOut.then((data) => {
    logger.notice('Wrote Result to Kinesis stream')
    resolve(data)
  }).catch((err) => {
    logger.error('FAILED TO PUT TO KINESIS')
    resolve(err)
  })
})
