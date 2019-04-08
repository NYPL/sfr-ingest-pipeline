import { Consumer } from 'sqs-consumer'
import { runAccessibilityReport } from './src/accessibility_report.js'
import { resultHandler } from './src/kinesis_out.js'
import { setEnv } from './src/env_config.js'
import logger from './src/helpers/logger'

// Invokes dotenv to load specific env variables from environment specific files
setEnv()

/*
 * Creates a long polling application that listens to the AWS SQS STREAM provided
 * in an environment variable. This manager method invokes the accessiblilty
 * report generator method and places the results in an Kinesis stream to be read
 * by the database manager function
 *
 * By default this checks for new messages every 20 seconds.
*/

let dataBlock

const app = Consumer.create({
  queueUrl: process.env.EBOOK_SOURCE_QUEUE,
  /*
   * @async
   * Fires when a message is received.
  */
  handleMessage: async (message) => {
    logger.info('Receiving ePub scoring request')
    dataBlock = JSON.parse(message.Body)
    logger.info(`Generating report for ePub file ${dataBlock.fileKey}`)

    const reportData = await runAccessibilityReport(dataBlock.fileKey)

    logger.info(`Outputting report data for ${dataBlock.fileKey}`)
    resultHandler(reportData, dataBlock, 200)
  }
})

// Generic error handler for the sqs-consumer app
app.on('error', (err) => {
  logger.error(err.message)
  resultHandler(err, dataBlock, 500)
})

// Error handler fired if the SQS message could not be parsed
app.on('processing_error', (err) => {
  logger.error(err.message)
  resultHandler(err, dataBlock, 500)
})

// Start the app. Can be started as multiple processes with pm2
app.start()
