const config = require('config')
const express = require('express')
const bodyParser = require('body-parser')
const logger = require('./lib/logger')
const SwaggerParser = require('swagger-parser')
const swaggerDocs = require('./swagger.v0.1.json')

require('dotenv').config()

var app = express()
app.logger = logger

app.use(bodyParser.json())

app.all('*', function (req, res, next) {
    res.header('Access-Control-Allow-Origin', '*')
    res.header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    res.header('Access-Control-Allow-Headers', 'Content-Type')
    next()
})

// Versioning
// The API implements a new version when breaking changes are introduced
// Different versions are routed off a base component in the URL
// By default the API will implment v1, though this behavior can easily be 
// altered at a future point.
// Further, old/deprecated versions can eventually be disabled.
const v1 = require('./routes/v1/v1')
const v2 = require('./routes/v2/v2')
app.use('/v2', v2)
app.use('/v1', v1)
app.use('/', v1)

// TODO: Implement different Swagger doc versions for versions of the API
app.get('/research-now/swagger', function (req, res) {
    res.send(swaggerDocs)
})

app.get('/research-now/swagger-test', function (req, res) {
    SwaggerParser.validate(swaggerDocs, (err, api) => {
      if (err) res.send(err)
      else res.send(`API name: ${api.info.title}, Version: ${api.info.version}`)
    })

})

const port = process.env.PORT || config['port']

app.listen(port, function () {
  app.logger.info('Server started on port ' + port)
})

module.exports = app
