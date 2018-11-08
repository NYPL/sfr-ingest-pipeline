import {ApolloClient} from 'apollo-client'
import gql from 'graphql-tag'
import fetch from 'node-fetch'
import {createHttpLink} from 'apollo-link-http'
import {setContext} from 'apollo-link-context'
import {InMemoryCache} from 'apollo-cache-inmemory'
import ApolloLinkTimeout from 'apollo-link-timeout'

import {parseRDF} from './src/parseRDF'

const httpLink = createHttpLink({
    uri: "https://api.github.com/graphql",
    fetch: fetch
})

const timeoutLink = new ApolloLinkTimeout(20000)

const timeoutHttpLink = timeoutLink.concat(httpLink)

const authLink = setContext((_, {headers}) => {
    const token = "d104c98efb88fde95573a69194e0a37e686ded6e"
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

const getRepos = () => {
    let first = 25
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

const getRDF = (repo) => {
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
        parseRDF(data)
    }).catch(err => {
        console.log(err)
    })
}

const sleep = (ms, mult) => {
    return new Promise(resolve => setTimeout(resolve, ms*mult))
}

exports.handler = async (event, context, callback) => {
    let success = false
    let tries = 0
    do {
        if(success == false) await sleep(15000, tries)
        success = await getRepos()
        tries++
    } while (success == false && tries < 3)

    if(success == false) return

    let repoInfo = success
    repoInfo.forEach(repo => {
        getRDF(repo)
    })

}
