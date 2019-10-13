import { getRDF, getRepos, addCoverFile } from './src/githubDataFetch'
import Kinesis from './src/kinesisOutput'
import Helpers from './src/fetchHelpers'
import logger from './src/helpers/logger'

exports.retrieveRepos = async () => {
  let success = false
  let tries = 0

  /* eslint-disable no-await-in-loop */
  do {
    logger.notice('Attempting to retrieve records from GITenberg')
    if (success === false) await Helpers.sleep(10000, tries)
    success = await getRepos()
    tries += 1
  } while (success === false && tries < process.env.REPO_RETRIES)
  /* eslint-enable no-await-in-loop */

  return success
}

exports.getRepoData = async (repoInfo, lcRels) => {
  const rdfValue = await getRDF(repoInfo, lcRels)
  await addCoverFile(repoInfo, rdfValue)
  return rdfValue
}

exports.handler = async (event, context, callback) => {
  const success = await exports.retrieveRepos()

  if (success === false) {
    logger.error('Github API request returned too many 5XX errors')
    return callback(new Error('Github API request returned too many 5XX errors'))
  }

  const lcRels = await Helpers.loadLCRels()
  const repoInfo = success
  if (repoInfo.length === 0) {
    logger.notice('No updates made in the fetch period to GITenberg')
    const emptyResult = {
      source: 'gutenberg',
      status: 204,
      message: 'No records updated in fetch period',
    }
    Kinesis.resultHandler(emptyResult)
    return callback(null, 'No updated records found')
  }

  for (let i = 0; i < repoInfo.length; i += 1) {
    // eslint-disable-next-line no-await-in-loop
    const metadataRec = await exports.getRepoData(repoInfo[i], lcRels)
    logger.debug('Processed GITenberg record')
    // Kinesis.resultHandler(metadataRec)
  }

  logger.notice('Successfully updated records')
  return callback(null, 'Successfully updated records')
}
