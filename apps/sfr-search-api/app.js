const config = require('config')
const express = require('express')
const bodyParser = require('body-parser')
const SwaggerParser = require('swagger-parser')
const swaggerUI = require('swagger-ui-express')
const logger = require('./lib/logger')
const swaggerDocs = require('./swagger.v3.json')

require('dotenv').config()

const { v3Router } = require('./routes/v3/v3')
const { v2Router } = require('./routes/v2/v2')
const { v1Router } = require('./routes/v1/v1')

const app = express()
app.logger = logger

app.use(bodyParser.json())

app.all('*', (req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*')
  res.header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
  res.header('Access-Control-Allow-Headers', 'Content-Type')
  next()
})

// Versioning
// The API implements a new version when breaking changes are introduced
// Different versions are routed off a base component in the URL
// By default the API will implement v1, though this behavior can easily be
// altered at a future point.
// Further, old/deprecated versions can eventually be disabled.

app.use('/v3', v3Router)
app.use('/v2', v2Router)
app.use('/v1', v1Router)
app.use('/', v1Router) // Controls default version of app

// TODO: Implement different Swagger doc versions for versions of the API
app.get('/research-now/swagger', (req, res) => {
  res.send(swaggerDocs)
})

app.use('/research-now/swagger-ui', swaggerUI.serve, swaggerUI.setup(swaggerDocs))

app.get('/research-now/swagger-test', (req, res) => {
  SwaggerParser.validate(swaggerDocs, (err, api) => {
    if (err) res.send(err)
    else res.send(`API name: ${api.info.title}, Version: ${api.info.version}`)
  })
})

const port = process.env.PORT || config.port

const server = app.listen(port, () => {
  app.logger.info(`Server started on port ${port}`)
})

module.exports = server
