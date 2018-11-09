import {ApolloClient} from 'apollo-client'
import gql from 'graphql-tag'
import fetch from 'node-fetch'
import {createHttpLink} from 'apollo-link-http'
import {setContext} from 'apollo-link-context'
import {InMemoryCache} from 'apollo-cache-inmemory'
import ApolloLinkTimeout from 'apollo-link-timeout'
import moment from 'moment'

import { parseRDF } from './parseRDF'

const httpLink = createHttpLink({
    uri: "https://api.github.com/graphql",
    fetch: fetch
})

const timeoutLink = new ApolloLinkTimeout(20000)

const timeoutHttpLink = timeoutLink.concat(httpLink)

const authLink = setContext((_, {headers}) => {
    const token = process.env.GITHUB_API_TOKEN
    return {
        headers: {
            authorization: token ? `Bearer ${token}` : ""
        }
    }
})

const client = new ApolloClient({
    link: authLink.concat(timeoutHttpLink),
    cache: new InMemoryCache()
})

const pgIDRegex = /([0-9]+)$/

export const getRepos = () => {
    let first = 25
    let fetchBoundary = moment().subtract(process.env.UPDATE_MAX_AGE_DAYS, 'days')
    let repoIDs = []
    return new Promise((resolve, reject) => {
        client.query({
            query: gql`
                {
                    organization(login:\"GITenberg\") {
                        repositories(orderBy:{direction:DESC, field:UPDATED_AT}, first:${first}) {
                            nodes {
                                id, name, resourcePath, url, updatedAt
                            }
                        }
                    }
                }
            `,
        }).then(data => {
            let repoList = data["data"]["organization"]["repositories"]["nodes"]
            repoList.forEach((repo) => {
                let updatedAt = moment(repo["updatedAt"])
                if (updatedAt.isBefore(fetchBoundary)) return
                let name = repo["name"]

                let idnoMatch = pgIDRegex.exec(name)
                if(!idnoMatch){
                    console.log(repo)
                    return
                }
                let idno = idnoMatch[0]
                repoIDs.push([name, idno])
            })
            resolve(repoIDs)
        })
        .catch(err => {
            console.log(err)
            resolve(false)
        })
    })
}

export const getRDF = (repo, lcRels) => {
    return new Promise((resolve, reject) => {
        let repoName = repo[0]
        let gutID = repo[1]
        let rdfPath = "master:pg" + gutID + ".rdf"
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
            parseRDF(data, lcRels, (rdfData) => {
                resolve({
                    "gutenbergID": gutID,
                    "data": rdfData,
                    "status": 200,
                    "message": "Retrieved Gutenberg Metadata"
                })
            })
        }).catch(err => {
            console.log(err)
            reject({
                "gutenbergID": gutID,
                "data": err,
                "status": 500,
                "message": "Error in parsing Gutenberg Record"
            })
        })
    })
}
