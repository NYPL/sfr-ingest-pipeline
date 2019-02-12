var config = require('config')
var express = require('express')
var bodyParser = require('body-parser')
var logger = require('./lib/logger')
var elasticsearch = require('elasticsearch')
var SwaggerParser = require('swagger-parser')
const pjson = require('./package.json')
const swaggerDocs = require('./swagger.v0.1.json')

require('dotenv').config()

var app = express()
app.logger = logger

app.use(bodyParser.json())

app.client = new elasticsearch.Client({
    host: process.env.ELASTICSEARCH_HOST
})


app.all('*', function (req, res, next) {
    res.header('Access-Control-Allow-Origin', '*')
    res.header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    res.header('Access-Control-Allow-Headers', 'Content-Type')
    next()
})

// Routes
// The Search Endpoints
require('./routes/search')(app)
// Single Record Lookup Endpoint
require('./routes/work')(app)

// Test that express routes are working.
app.get('/', function (req, res) {
    res.send(pjson.version)
})

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
