const express = require('express')

const pjson = require('./../../package.json')

// v2 of the SFR API. This is a simple test endpoint to demonstrate the 
// ability to route users based on a version provided. No search/lookup
// abilities have been implemented here yet. The structure will be similar to 
// the v1 endpoints, but will utilize a different ElasticSearch endpoint

const v2Router = express.Router()

v2Router.get('/', function (req, res) {
    res.send({
        codeVersion: pjson.version,
        apiVersion: 'v2'
    })
})

// Temporary demonstration endpoint, to be removed when v2 becomes functional
v2Router.get('/test', function(req, res) {
    res.send({
        'testing': 'A v2 only endpoint'
    })
})

module.exports = v2Router