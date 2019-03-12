const express = require('express')
const pjson = require('./../../package.json')
const logger = require('./../../lib/logger')
const elasticsearch = require('elasticsearch')

// Initialize v1 routes
// These are accessibile at /v1/* or /*
const v1Router = express.Router()

// Set ElasticSearch endpoint for routes
v1Router.client = new elasticsearch.Client({
  host: process.env.ELASTICSEARCH_HOST
})

// Initialize logging
v1Router.logger = logger

// Load endpoints for version
require('./search')(v1Router)
require('./work')(v1Router)

// Return basic status update on API
v1Router.get('/', function (req, res) {
  res.send({
    codeVersion: pjson.version,
    apiVersion: 'v1'
  })
})

module.exports = v1Router
