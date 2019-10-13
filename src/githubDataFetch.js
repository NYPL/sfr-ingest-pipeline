import { InMemoryCache } from 'apollo-cache-inmemory'
import { ApolloClient } from 'apollo-client'
import { setContext } from 'apollo-link-context'
import { onError } from 'apollo-link-error'
import { createHttpLink } from 'apollo-link-http'
import ApolloLinkTimeout from 'apollo-link-timeout'
import Axios from 'axios'
import fs from 'fs'
import gql from 'graphql-tag'
import fetch from 'node-fetch'
import moment from 'moment'
import yaml from 'js-yaml'

import RDFParser from './parseRDF'
import logger from './helpers/logger'
import { LCSHYamlType, LCCYamlType } from './helpers/yaml'

const httpLink = createHttpLink({
  uri: 'https://api.github.com/graphql',
  fetch,
})

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, location, path }) => {
      logger.error(`Error in GraphQL Query: ${message}, Location: ${location}, Path: ${path}`)
    })
  } else if (networkError) {
    logger.error(`GraphQL Connection Error: ${networkError}`)
  }
})

const errorHttpLink = errorLink.concat(httpLink)

const timeoutLink = new ApolloLinkTimeout(20000)

const errorTimeoutHttpLink = timeoutLink.concat(errorHttpLink)

// eslint-disable-next-line no-unused-vars
const authLink = setContext((_, { headers }) => {
  const token = process.env.GITHUB_API_TOKEN
  return {
    headers: {
      authorization: token ? `Bearer ${token}` : '',
    },
  }
})

// We don't want to cache queries because we are always looking for new records
// Since this is only trigged at most a few times a day (and probably less than
// that) it should not make an impact (this is responding to a lambda, not users)
const apolloOpts = {
  watchQuery: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'ignore',
  },
  query: {
    fetchPolicy: 'no-cache',
    errorPolicy: 'all',
  },
}

const client = new ApolloClient({
  link: authLink.concat(errorTimeoutHttpLink),
  cache: new InMemoryCache(),
  defaultOptions: apolloOpts,
})

const pgIDRegex = /([0-9]+)$/

const getRepos = () => {
  const first = 25
  const fetchBoundary = moment().subtract(process.env.UPDATE_MAX_AGE_DAYS, 'days')
  const repoIDs = []
  return new Promise((resolve) => {
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
          `,
    }).then((data) => {
      // If data is null, the GraphQL request errored out and should return false
      if (data.data === 'null') resolve(false)

      const repoList = data.data.organization.repositories.nodes
      repoList.forEach((repo) => {
        const updatedAt = moment(repo.pushedAt)
        if (updatedAt.isBefore(fetchBoundary)) return
        const { name, url } = repo

        const idnoMatch = pgIDRegex.exec(name)
        if (!idnoMatch) return

        const idno = idnoMatch[0]

        repoIDs.push([name, idno, url])
      })
      resolve(repoIDs)
    })
      .catch(() => resolve(false))
  })
}
/* eslint-disable prefer-promise-reject-errors */
const getRDF = (repo, lcRels) => new Promise((resolve) => {
  const repoName = repo[0]
  const gutID = repo[1]
  const repoURI = repo[2]
  const rdfPath = `master:pg${gutID}.rdf`
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
        `,
  }).then((data) => {
    RDFParser.parseRDF(data, gutID, repoURI, lcRels, (err, rdfData) => {
      if (err) {
        resolve({
          recordID: gutID,
          source: 'gutenberg',
          type: 'work',
          method: 'insert',
          data: err,
          status: 500,
          message: 'Could not parse Gutenberg Metadata',
        })
      } else {
        resolve({
          recordID: gutID,
          source: 'gutenberg',
          type: 'work',
          method: 'insert',
          data: rdfData,
          status: 200,
          message: 'Retrieved Gutenberg Metadata',
        })
      }
    })
  }).catch((err) => {
    resolve({
      recordID: gutID,
      source: 'gutenberg',
      type: 'work',
      method: 'insert',
      data: err,
      status: 500,
      message: 'Error in parsing Gutenberg Record',
    })
  })
})

const fetchCoverFile = async (gutenPath, repoName, filePath) => {
  const fileURL = gutenPath.replace('ebooks', 'files')
  const coverURL = `${fileURL}/${filePath}`
  const fileWriter = fs.createWriteStream(repoName)
  const fileResp = await Axios({ url: coverURL, method: 'GET', responseType: 'stream' })
  fileResp.data.pipe(fileWriter)
  return new Promise((resolve, reject) => {
    fileWriter.on('finish', resolve(repoName))
    fileWriter.on('error', reject)
  })
}

const getMetadataFile = (repo) => new Promise((resolve, reject) => {
  client.query({
    query: gql`
            {
              repository(owner:\"GITenberg\", name:\"${repo}\"){
                object(expression:\"master:metadata.yaml\"){
                  id
                  ... on Blob {text}
                }
            }
          }
        `,
  }).then((data) => {
    try {
      const gutenSchema = yaml.Schema.create([LCSHYamlType, LCCYamlType])
      const yamlConfig = yaml.load(data.data.repository.object.text, { schema: gutenSchema })
      resolve(yamlConfig)
    } catch (err) {
      reject(err)
    }
  }).catch((err) => {
    reject(err)
  })
})

const addCoverFile = async (repo, metadata) => {
  const repoName = repo[0]
  let repoMetadata
  try {
    repoMetadata = await getMetadataFile(repoName)
  } catch (err) {
    logger.error(err)
  }
  if (repoMetadata.covers) {
    logger.debug(`Found covers in ${repoName}`)
    // eslint-disable-next-line consistent-return
    repoMetadata.covers.forEach(async (coverMeta) => {
      logger.debug(`Cover Type: ${coverMeta.cover_type} | Cover Path: ${coverMeta.image_path}`)
      if (coverMeta.cover_type !== 'generated') {
        // eslint-disable-next-line no-underscore-dangle
        const coverFile = await fetchCoverFile(repoMetadata.url, repoMetadata._repo, coverMeta.image_path)
        // return coverFile
        console.log(coverFile)
      }
    })
  }
  return null
}

/* eslint-enable prefer-promise-reject-errors */

module.exports = {
  getRepos,
  getRDF,
  addCoverFile,
}
