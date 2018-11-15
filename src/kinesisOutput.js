import AWS from 'aws-sdk'
import logger from './helpers/logger'

AWS.config.update({
  region: 'us-east-1',
  logger: process.stdout
})

var customKinEndpoint
if (process.env.AWS_KINESIS_ENDPOINT) {
  customKinEndpoint = {
    endpoint: process.env.AWS_KINESIS_ENDPOINT
  }
}

const kinesis = new AWS.Kinesis(customKinEndpoint)

exports.resultHandler = (handleResp) => {
  return new Promise((resolve, reject) => {
    let outParams = {
      Data: JSON.stringify(handleResp),
      PartitionKey: process.env.AWS_KINESIS_STREAMID,
      StreamName: process.env.AWS_KINESIS_STREAMNAME
    }

    let kinesisOut = kinesis.putRecord(outParams).promise()
    kinesisOut.then((data) => {
      logger.notice('Wrote Result to Kinesis stream')
      resolve(data)
    }).catch((err) => {
      logger.error('FAILED TO PUT TO KINESIS')
      resolve(err)
    })
  })
}
