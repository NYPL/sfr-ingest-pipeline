const express = require('express')
const elasticsearch = require('elasticsearch')
const pjson = require('./../../package.json')
const logger = require('./../../lib/logger')
const { v1Search } = require('./search')
const { v1Work } = require('./work')

// Initialize v1 routes
// These are accessible at /v1/* or /*
const v1Router = express.Router()

// Set ElasticSearch endpoint for routes
v1Router.client = new elasticsearch.Client({
  host: process.env.ELASTICSEARCH_HOST,
})

// Initialize logging
v1Router.logger = logger

// Load endpoints for version
v1Search(v1Router)
v1Work(v1Router)

// Return basic status update on API
v1Router.get('/', (req, res) => {
  res.send({
    codeVersion: pjson.version,
    apiVersion: 'v1',
  })
})

module.exports = { v1Router }
