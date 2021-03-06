import ace from '@daisy/ace'
import axeRunner from '@daisy/ace-axe-runner-puppeteer'
import fs from 'fs'
import AWS from 'aws-sdk'
import logger from './helpers/logger'

const STARTING_SCORE = 10 // Defines total possible score for accessibility reports
const SCORE_DIVISOR = 4 // Increase for harsher scores, decrease for easier

/**
 * Main method that handles logic around generating Accessibility Reports.
 * Stores the source ePub archive file in the /tmp directory (cleared hourly)
 * and invokes the ACE reporting tool to generate a raw report, which is then
 * parsed and a generated score is added to a report summary
 * 
 * @async
 * @param {string} fileKey A full path to an object in the ePub S3 bucket
 * @returns {object} A full report object including the full JSON output by ACE, a brief summary and a generated score
*/
exports.runAccessibilityReport = async (fileKey) => {
  return new Promise(async (resolve, reject) => {
    let tmpFile, report
    try {
      tmpFile = await exports.downloadEpubFile(fileKey)
    } catch (e) {
      logger.error(e)
      reject(e)
      return
    }

    const aceOpts = {
      cwd: __dirname,
      outdir: null,
      tmpdir: '/tmp',
      verbose: false,
      silent: true
    }
    logger.info('Generating ACE Report')
    try {
      report = await ace(tmpFile.path, aceOpts, axeRunner)
    } catch (e) {
      logger.error(e)
      reject(e)
      return
    }
    logger.info('Parsing ACE Report')
    const reportSummary = exports.parseReport(report)
    logger.info('Returning ACE Report')
    resolve(reportSummary)
  })
}

/**
 * Accesses and stores an .epub file (zipped archive) from the S3 bucket defined
 * in the current environment variables.
 * 
 * @async
 * @param {string} s3Key The key to an S3 object (full path)
 * @returns {object} A local representation of the .epub file
*/
exports.downloadEpubFile = async (s3Key) => {
  return new Promise((resolve, reject) => {
    const s3 = new AWS.S3()
    const s3Params = {
      Bucket: 'simplye-research-epubs',
      Key: s3Key
    }
    logger.debug(`Downloading file ${s3Key} from S3`)
    const file = exports.createTmpFile()
    const s3Stream = s3.getObject(s3Params).createReadStream()
    s3Stream.on('error', (err) => { reject(err) })
    file.on('error', (err) => {
      logger.error(err)
      reject(err)
    })
    file.on('close', () => {
      logger.debug(`Storing downloaded file in ${file.path}`)
      resolve(file)
    })
    s3Stream.pipe(file)
  })
}

/**
 * Generate a temporary file where the .epub can be stored. Utilizes multiple
 * Math.random() calls of varying lengths to generate a random string
 *
 * @returns {object} A WriteStream object
*/
exports.createTmpFile = () => {
  const tmpFile = '/tmp/' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
  logger.debug(`Creating tmp file for epub at ${tmpFile.path}`)
  return fs.createWriteStream(tmpFile)
}

/**
 * Parses the full report object returned by ACE and totals the number of
 * violations received by severity level. These totals are then used to generate
 * an overall score. Both sets of metadata are added with the report JSON to an
 * output object which will be stored in the SFR persistence layer
 *
 * @param {Object} report A report generated by ACE from an .epub file
 * @returns {Object} A wrapper object containing the ACE report and metadata derived from its contents
*/
exports.parseReport = (report) => {
  const mainReport = report[1]
  const assertions = mainReport.assertions
  const timeRun = mainReport['dct:date']
  const aceVersion = mainReport['earl:assertedBy']['doap:release']['doap:revision']
  const assertionOut = exports.parseAssertions(assertions)
  const vioObj = {}
  Object.keys(assertionOut.violations).forEach(key => {
    const value = assertionOut.violations[key]
    logger.debug(`Found ${value} ${key} violations`)
    vioObj[key] = value
  })
  return {
    json: mainReport, // ACE report data
    aceVersion: aceVersion, // Version of ACE tool used, extracted from report
    timestamp: timeRun, // Time of report generation, extracted from report
    score: assertionOut.score, // SFR accessibility score, calculated from violations
    violations: vioObj // Summary of violations extracted from ACE report
  }
}

/**
 * Extracts the total number of violations by severity level, without regard
 * to the specific violation that occured. These are used to generate the overall
 * accessibility score.
 *
 * @param {Object} assertions Array of assertions from the ACE reporting tool
 * @return {Object} Metadata block containg the assertion totals and calculated score
*/
exports.parseAssertions = (assertions) => {
  logger.debug(`Parsing ${assertions.length} assertions`)

  // Object to be returned by this method
  const output = {
    score: 0,
    violations: {
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 0
    }
  }

  // Iterate the assertions received and extract the severity
  assertions.map((assertion) => {
    const tests = assertion.assertions
    tests.map((test) => {
      const errType = test['earl:test']['earl:impact']
      logger.debug(`Found new ${errType} violation`)
      output.violations[errType]++
    })
  })

  // Use the summed violations to calculate an accessibility score
  logger.debug('Calculating accessibility score')
  const score = exports.calculateScore(output.violations)
  if (score > 0) output['score'] = score
  return output
}

/**
 * Generates a summary score based on the number and severity of violations
 * found in the .epub file. This algorithm takes a starting score, defined above,
 * and subtracts a certain number defined by an exponential scale.
 *
 * @param {Object} violations An object containing counts of violations by severity
 * @returns {float} The calculated score for the .epub file
*/
exports.calculateScore = (violations) => {
  let score = STARTING_SCORE
  let i = 0
  Object.keys(violations).forEach(key => {
    const value = violations[key]
    logger.debug(`Factoring ${value} ${key} violations in score`)
    score -= value / (Math.pow(SCORE_DIVISOR, i))
    i++ // Decreases the amount subtracted for each level of severity
  })

  return score
}
