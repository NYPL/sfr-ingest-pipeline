import { getRepos, getRDF } from './src/githubDataFetch'
import { resultHandler } from './src/kinesisOutput'
import { sleep, loadLCRels } from './src/fetchHelpers'

exports.handler = async (event, context, callback) => {
    let success = false
    let tries = process.env.REPO_RETRIES
    do {
        if(success == false) await sleep(10000, tries)
        success = await getRepos()
        tries++
    } while (success == false && tries < 3)

    if(success == false) return
    let lcRels = await loadLCRels()
    let repoInfo = success
    for(let i = 0; i < repoInfo.length; i++){
        let metadataRec = await getRDF(repoInfo[i], lcRels)
        resultHandler(metadataRec)
    }

}
