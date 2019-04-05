import ace from '@daisy/ace-core'
import fs from 'fs'
import AWS from 'aws-sdk'
import logger from './helpers/logger'

const STARTING_SCORE = 10
const SCORE_DIVISOR = 4

exports.runAccessibilityReport = async (fileKey) => {
  return new Promise(async (res, reject) => {
    let tmpFile, report
    try{
      tmpFile = await exports.downloadEpubFile(fileKey)
    } catch(e) {
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
    try{
      report = await ace(tmpFile.path, aceOpts)
    } catch(e) {
      logger.error(e)
      reject(e)
      return
    }
    logger.info('Parsing ACE Report')
    const reportSummary = exports.parseReport(report)
    logger.info('Returing ACE Report')
    res(reportSummary)

  })
}

exports.downloadEpubFile = async (s3Key) => {
  return new Promise ((res, reject) => {
    const s3 = new AWS.S3()
    const s3Params = {
      Bucket: 'simplye-research-epubs',
      Key: s3Key
    }
    logger.debug(`Downloading file ${s3Key} from S3`)
    const file = exports.createTmpFile()
    s3.getObject(s3Params).createReadStream().pipe(file).on('close', () => {
      logger.debug(`Storing downloaded file in ${file.path}`)
      res(file)
    }).on('error', (err) => {
      logger.error(err)
      reject(err)
    })
  })
  
}

exports.createTmpFile = () => {
  console.log('Saving file in tmp directory')
  const tmpFile = '/tmp/' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
  return fs.createWriteStream(tmpFile)
}

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
    json: mainReport,
    aceVersion: aceVersion,
    timestamp: timeRun,
    score: assertionOut.score,
    violations: vioObj
  }
}

exports.parseAssertions = (assertions) => {
  logger.debug(`Parsing ${assertions.length} assertions`)
  const output = {
    score: 0,
    violations: {
      critial: 0,
      serious: 0,
      moderate: 0,
      minor: 0
    }
  }
  assertions.map((assertion) => {
    const tests = assertion.assertions
    tests.map((test)=> {
      const errType = test['earl:test']['earl:impact']
      logger.debug(`Found new ${errType} violation`)
      output.violations[errType]++
    })
  })

  logger.debug('Calculating accessibility score')
  const score = exports.calculateScore(output.violations)
  if (score > 0) output['score'] = score
  return output
}

exports.calculateScore = (violations) => {
  let score = STARTING_SCORE
  let i = 0
  Object.keys(violations).forEach(key => {
    const value = violations[key]
    logger.debug(`Factoring ${value} ${key} violations in score`)
    score -= value/(Math.pow(SCORE_DIVISOR, i))
    i++
  })

  return score
}
