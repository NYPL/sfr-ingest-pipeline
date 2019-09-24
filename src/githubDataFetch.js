import { ApolloClient } from 'apollo-client'
import gql from 'graphql-tag'
import fetch from 'node-fetch'
import { createHttpLink } from 'apollo-link-http'
import { setContext } from 'apollo-link-context'
import { onError } from 'apollo-link-error'
import { InMemoryCache } from 'apollo-cache-inmemory'
import ApolloLinkTimeout from 'apollo-link-timeout'
import moment from 'moment'
import axios from 'axios'

import RDFParser from './parseRDF'
import logger from './helpers/logger'

const httpLink = createHttpLink({
  uri: 'https://api.github.com/graphql',
  fetch: fetch
})

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.map(({ message, location, path }) => {
      logger.error(`Error in GraphQL Query: ${message}, Location: ${location}, Path: ${path}`)
    })
  } else if (networkError) {
    logger.error(`GraphQL Connection Error: ${networkError}`)
  }
})

const errorHttpLink = errorLink.concat(httpLink)

const timeoutLink = new ApolloLinkTimeout(20000)

const errorTimeoutHttpLink = timeoutLink.concat(errorHttpLink)

const authLink = setContext((_, { headers }) => {
  const token = process.env.GITHUB_API_TOKEN
  return {
    headers: {
      authorization: token ? `Bearer ${token}` : ''
    }
  }
})

// We don't want to cache queries because we are always looking for new records
// Since this is only trigged at most a few times a day (and probably less than
// that) it should not make an impact (this is responding to a lambda, not users)
const apolloOpts = {
  watchQuery: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'ignore'
  },
  query: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'all'
  }
}

const client = new ApolloClient({
  link: authLink.concat(errorTimeoutHttpLink),
  cache: new InMemoryCache(),
  defaultOptions: apolloOpts
})

const pgIDRegex = /([0-9]+)$/

exports.getRepos = () => {
  let first = 25
  let fetchBoundary = moment().subtract(process.env.UPDATE_MAX_AGE_DAYS, 'days')
  let repoIDs = []
  return new Promise((resolve, reject) => {
    client.query({
      query: gql`
              {
                organization(login:\"GITenberg\") {
                  repositories(orderBy:{direction:DESC, field:PUSHED_AT}, first:${first}) {
                  nodes {
                    id, name, resourcePath, url, pushedAt
                  }
                }
              }
            }
          `
    }).then(data => {

      // If data is null, the GraphQL request errored out and should return false
      if (data['data'] == 'null') resolve(false)

      let repoList = data['data']['organization']['repositories']['nodes']
      repoList.forEach((repo) => {
        let updatedAt = moment(repo['pushedAt'])
        if (updatedAt.isBefore(fetchBoundary)) return
        let name = repo['name']

        let idnoMatch = pgIDRegex.exec(name)
        if (!idnoMatch) return

        let idno = idnoMatch[0]

        let url = repo['url']

        repoIDs.push([name, idno, url])
      })
      resolve(repoIDs)
    })
      .catch(err => {
        resolve(false)
      })
  })
}

exports.getRepoRange = async (startPos, repoCount) => {
  const repoIDs = []
  const startPage = (startPos - (startPos % 100)) / 100
  let endPage = (((startPos + repoCount) - ((startPos + repoCount) % 100)) / 100)
  const finalPageSize = repoCount % 100 == 0 ? 100 : repoCount % 100 
  let pageSize = 100
  if(endPage == startPage){ endPage++ }
  console.log(startPage, endPage)
  for(let i = startPage; i < endPage; i++){
    try{
      if(i == endPage - 1){
        pageSize = finalPageSize
      }
      let pageRepos = await exports.loadRepoPage(i, pageSize)
      repoIDs.push(...pageRepos)
    } catch(err) {
      logger.error(err)
      return false
    }
  }
  return repoIDs
}

exports.loadRepoPage = (page, pageSize) => {
  const repoIDs = []
  return new Promise((resolve, reject) => {
    logger.debug(`Loading page ${page} of GITenberg repositories`)
      axios.get(`https://api.github.com/users/GITenberg/repos?page=${page}&per_page=${pageSize}`)
        .then(data => {
          const repos = data.data
          if (repos === null || repos.length == 0) resolve(false)
    
          repos.forEach((repo) => {
            let name = repo['name']
    
            let idnoMatch = pgIDRegex.exec(name)
            if (!idnoMatch) return
    
            let idno = idnoMatch[0]
    
            let url = repo.html_url
    
            repoIDs.push([name, idno, url])
          })
          resolve(repoIDs)
        })
        .catch(err => {
          reject(err)
        })
  })
}

/* eslint-disable prefer-promise-reject-errors */
exports.getRDF = (repo, lcRels) => {
  return new Promise((resolve, reject) => {
    let repoName = repo[0]
    let gutID = repo[1]
    let repoURI = repo[2]
    let rdfPath = 'master:pg' + gutID + '.rdf'
    client.query({
      query: gql`
              {
                repository(owner:\"GITenberg\", name:\"${repoName}\"){
                  object(expression:\"${rdfPath}\"){
                    id
                    ... on Blob {text}
                  }
              }
            }
          `
    }).then(data => {
      RDFParser.parseRDF(data, gutID, repoURI, lcRels, (err, rdfData) => {
        if (err) {
          resolve({
            'recordID': gutID,
            'source': 'gutenberg',
            'type': 'work',
            'method': 'insert',
            'data': err,
            'status': 500,
            'message': 'Could not parse Gutenberg Metadata'
          })
        } else {
          resolve({
            'recordID': gutID,
            'source': 'gutenberg',
            'type': 'work',
            'method': 'insert',
            'data': rdfData,
            'status': 200,
            'message': 'Retrieved Gutenberg Metadata'
          })
        }
      })
    }).catch(err => {
      resolve({
        'recordID': gutID,
        'source': 'gutenberg',
        'type': 'work',
        'method': 'insert',
        'data': err,
        'status': 500,
        'message': 'Error in parsing Gutenberg Record'
      })
    })
  })
}
/* eslint-enable prefer-promise-reject-errors */
