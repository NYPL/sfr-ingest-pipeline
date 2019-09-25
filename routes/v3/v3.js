const express = require('express')
const elasticsearch = require('elasticsearch')
const logger = require('../../lib/logger')
const pjson = require('../../package.json')
const { searchEndpoints } = require('./search')
const { workEndpoints } = require('./work')
const { utilEndpoints } = require('./utils')

// Create an instance of an Express router to handle requests to v2 of the API
const v3Router = express.Router()

// Initialize logging
v3Router.logger = logger

// Set ElasticSearch endpoint for routes
v3Router.client = new elasticsearch.Client({
  host: process.env.ELASTICSEARCH_HOST,
})

// Status endpoint to verify that v2 is available
v3Router.get('/', (req, res) => {
  res.send({
    codeVersion: pjson.version,
    apiVersion: 'v3',
  })
})

/**
 * Parses and returns the results of a query against the API.
 *
 * @param {Res} res An Express response object.
 * @param {Object} _resp The body of the response.
 * @param {Object} params An object representing the query made against the API.
 */
const respond = (res, _resp, params, type) => {
  const contentType = 'application/json'

  let resp = _resp
  if (contentType !== 'text/plain') resp = JSON.stringify(_resp, null, 2)

  v3Router.logger.info(`Search performed: ${JSON.stringify(params)}`)
  res.type(contentType)
  res.status(200).send({
    status: 200,
    data: JSON.parse(resp),
    timestamp: new Date().toISOString(),
    responseType: type,
  })
  return true
}

/**
 * Handle errors returned in the course of making a query.
 *
 * @param {Res} res An Express response object.
 * @param {Error} error An error received, to be parsed and returned as non-200 status.
 */
const handleError = (res, error, errType, errReason) => {
  v3Router.logger.error('Resources#handleError:', error)
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
  res.status(statusCode).send({
    status: statusCode,
    name: error.displayName || error.name,
    error: error.message ? error.message : error,
    type: errType || 'unknown',
    reason: errReason || 'unknown',
  })
  return false
}


// Load endpoints
searchEndpoints(v3Router, respond, handleError)
workEndpoints(v3Router, respond, handleError)
utilEndpoints(v3Router, respond, handleError)

module.exports = { v3Router, respond, handleError }
