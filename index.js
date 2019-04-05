import { Consumer } from 'sqs-consumer'
import { runAccessibilityReport } from './src/accessibility_report.js'
import { resultHandler } from './src/kinesis_out.js'
import { setEnv } from './src/env_config.js'
import logger from './src/helpers/logger'
setEnv()

const app = Consumer.create({
  queueUrl: process.env.EBOOK_SOURCE_QUEUE,
  handleMessage: async (message) => {
    logger.info('Receiving ePub scoring request')
    const dataBlock = JSON.parse(message.Body)
    logger.info(`Generating report for ePub file ${dataBlock.fileKey}`)

    const reportData = await runAccessibilityReport(dataBlock.fileKey)
    
    reportData.instanceID = dataBlock.instanceID
    reportData.identifier = dataBlock.identifier
    const report = {
      status: 200,
      code: 'accessibility',
      message: 'Created Accessibility Score',
      type: 'access_report',
      method: 'insert',
      data: reportData,
    }
    logger.info(`Outputting report data for ${dataBlock.fileKey}`)
    resultHandler(report)
  }
})

app.on('error', (err) => {
  logger.error(err.message)
})

app.on('processing_error', (err) => {
  logger.error(err.message)
})

app.start()