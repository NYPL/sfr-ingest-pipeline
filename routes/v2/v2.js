const express = require('express')
const logger = require('./../../lib/logger')
const elasticsearch = require('elasticsearch')
const pjson = require('./../../package.json')

// v2 of the SFR API. This is a simple test endpoint to demonstrate the
// ability to route users based on a version provided. No search/lookup
// abilities have been implemented here yet. The structure will be similar to
// the v1 endpoints, but will utilize a different ElasticSearch endpoint

const v2Router = express.Router()

// Initialize logging
v2Router.logger = logger

// Set ElasticSearch endpoint for routes
v2Router.client = new elasticsearch.Client({
  host: process.env.ELASTICSEARCH_HOST
})

v2Router.get('/', function (req, res) {
  res.send({
    codeVersion: pjson.version,
    apiVersion: 'v2'
  })
})

const respond = (res, _resp, params) => {
  const contentType = 'application/json'

  let resp = _resp
  if (contentType !== 'text/plain') resp = JSON.stringify(_resp, null, 2)

  v2Router.logger.info('Search performed: ' + JSON.stringify(params))
  res.type(contentType)
  res.status(200).send(resp)
  return true
}

const handleError = (res, error) => {
  v2Router.logger.error('Resources#handleError:', error)
  let statusCode = 500
  switch (error.name) {
    case 'InvalidParameterError':
      statusCode = 422
      break
    case 'NotFoundError':
      statusCode = 404
      break
    default:
      statusCode = 500
  }
  res.status(statusCode).send({ status: statusCode, name: error.name, error: error.message ? error.message : error })
  return false
}

// Load endpoints for version
const { searchEndpoints } = require('./search')
searchEndpoints(v2Router, respond, handleError)
const { workEndpoints } = require('./work')
workEndpoints(v2Router, respond, handleError)

module.exports = { v2Router, respond, handleError }
