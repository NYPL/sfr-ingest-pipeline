import AWS from 'aws-sdk'
import logger from './helpers/logger'

AWS.config.update({
  region: 'us-east-1',
  logger: process.stdout
})

var customKinEndpoint
if (process.env.ALT_AWS_ACCOUNT) {
  customKinEndpoint = {
    endpoint: process.env.ALT_AWS_ACCOUNT
  }
}

const kinesis = new AWS.Kinesis(customKinEndpoint)

exports.resultHandler = (handleResp) => {
  return new Promise((resolve, reject) => {
    let outParams = {
      Data: JSON.stringify(handleResp),
      PartitionKey: process.env.INGEST_SHARD,
      StreamName: process.env.INGEST_KINESIS
    }
    logger.debug(`Putting report in ${process.env.INGEST_KINESIS}`)
    /*
    let kinesisOut = kinesis.putRecord(outParams).promise()
    kinesisOut.then((data) => {
      resolve(data)
    }).catch((err) => {
      resolve(err)
    })
    */
  })
}