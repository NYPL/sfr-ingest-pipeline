var Elastic = require('elasticsearch')
require('dotenv').config()

function elasticsearchClient () {
    var client = new Elastic.Client({
        host: process.env.ELASTICSEARCH_HOST,
        log: 'trace'
    })

    this.healthCheck = function () {
        client.ping({
            requestTimeout: 30000,
        }, function (error) {
            if (error) {
                console.error('Cluster is unreachable')
            } else {
                console.log('Healthy instance!')
            }
        })
    }

    this.simpleSearch = function () {
        client.search({
            q: 'gutenberg'
        }).then(function (body) {
            var hits = body.hits.hits
            console.log(hits)
        }, function (error) {
            console.trace(error)
        })
    }
}

module.exports = { elasticsearchClient }
