import AWS from 'aws-sdk'
import logger from './helpers/logger'

AWS.config.update({
  region: 'us-east-1',
  logger: process.stdout
})

// If not using the standard AWS account defined on this machine, provide the Kinesis endpoint
var customKinEndpoint
if (process.env.ALT_AWS_ACCOUNT) {
  customKinEndpoint = {
    endpoint: process.env.ALT_AWS_ACCOUNT
  }
}

// Create a connection to the Kinesis service
const kinesis = new AWS.Kinesis(customKinEndpoint)

/*
 * Output a result object to the Kinesis stream. This can either contain a success
 * object with report data or an error object containing an error message. This
 * assumes that the stream these records are being placed in contains only one
 * shard
 * 
 * @param {object} reportData Full generated report containing ACE and derived metadata
 * @param {object} metaBlock Object containg metadata describing the source record
 * @param {integer} Status code (200/500)
 * 
 * @returns {object} Kinesis response object
*/
exports.resultHandler = (reportData, metaBlock, status) => {
  return new Promise((resolve) => {

    reportData.instanceID = metaBlock.instanceID
    reportData.identifier = metaBlock.identifier
    const report = {
      status: status,
      code: 'accessibility',
      report.type = 'access_report',
      data: reportData,
    }

    if(status === 200){
      report.message = 'Created Accessibility Score'
      report.method = 'insert'
    } else {
      report.message = 'Failed to create Accessiblity Score'
      report.method = 'error'
    }

    let outParams = {
      Data: JSON.stringify(report),
      PartitionKey: process.env.INGEST_SHARD,
      StreamName: process.env.INGEST_KINESIS
    }
    logger.debug(`Putting report in ${process.env.INGEST_KINESIS}`)
    
    let kinesisOut = kinesis.putRecord(outParams).promise()
    kinesisOut.then((data) => {
      resolve(data)
    }).catch((err) => {
      resolve(err)
    })
  })
}