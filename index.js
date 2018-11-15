import GitFetch from './src/githubDataFetch'
import Kinesis from './src/kinesisOutput'
import Helpers from './src/fetchHelpers'
import logger from './src/helpers/logger'

exports.retrieveRepos = async () => {
  let success = false
  let tries = 0

  do {
    logger.notice('Attempting to retrieve records from GITenberg')
    if (success === false) await Helpers.sleep(10000, tries)
    success = await GitFetch.getRepos()
    tries++
  } while (success === false && tries < process.env.REPO_RETRIES)

  return success
}

exports.getRepoData = async (repoInfo, lcRels) => {
  let rdfValue = await GitFetch.getRDF(repoInfo, lcRels)
  return rdfValue
}

exports.handler = async (event, context, callback) => {
  let success = await exports.retrieveRepos()

  if (success === false) {
    logger.error('Github API request returned too many 5XX errors')
    return callback(new Error('Github API request returned too many 5XX errors'))
  }

  let lcRels = await Helpers.loadLCRels()
  let repoInfo = success
  if (repoInfo.length === 0) {
    logger.notice('No updates made in the fetch period to GITenberg')
    return callback(new Error('No updates made in the fetch period to GITenberg'))
  }

  for (let i = 0; i < repoInfo.length; i++) {
    let metadataRec = await exports.getRepoData(repoInfo[i], lcRels)
    logger.debug('Processed GITenberg record')
    Kinesis.resultHandler(metadataRec)
  }

  logger.notice('Successfully updated records')
  return callback(null, 'Successfully updated records')
}
