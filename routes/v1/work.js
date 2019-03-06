// const config = require('config')
const bodybuilder = require('bodybuilder')
const { ElasticSearchError } = require('../../lib/errors')

module.exports = function (app) {
  const respond = (res, _resp, params) => {
    const contentType = 'application/json'

    let resp = _resp

    const respLen = resp['hits']['hits'].length

    if (respLen < 1) return handleError(res, new ElasticSearchError('Could not locate a record with that identifier'))
    else if (respLen > 1) return handleError(res, new ElasticSearchError('Returned multiple records, identifier lacks specificity'))

    const singleResp = resp['hits']['hits'][0]['_source']

    if (contentType !== 'text/plain') resp = JSON.stringify(singleResp, null, 2)

    app.logger.info('Search performed: ' + JSON.stringify(params))
    res.type(contentType)
    res.status(200).send(resp)
    return true
  }

  const handleError = (res, error) => {
    app.logger.error('Resources#handleError:', error)
    console.log(error)
    console.log(error.name)
    let statusCode = 500
    switch (error.name) {
      case 'InvalidParameterError':
        statusCode = 422
        break
      case 'NotFoundError':
        statusCode = 404
        break
      case 'ElasticSearchError':
        statusCode = 522
        break
      default:
        statusCode = 500
    }
    res.status(statusCode).send({ status: statusCode, name: error.name, error: error.message ? error.message : error })
    return false
  }

  app.get(`/api/v0.1/sfr/work`, function (req, res) {
    const recordID = req.query.recordID
    // let idType = req.query.type

    //
    // A potential feature is to limit look-ups by type of identifier, but the
    // elasticsearch mapping is not currently configured to support that properly
    // It will be in production, so I'm making a TO-DO note about that
    //
    const body = bodybuilder()
      .orQuery('term', 'uuid.keyword', recordID)
      .orQuery('term', 'ids.identifier.keyword', recordID)
      .orQuery('term', 'instances.ids.identifier.keyword', recordID)

    const params = {
      index: process.env.ELASTICSEARCH_INDEX,
      body: body.build()
    }
    console.log(body.build())
    return app.client.search(params, { baseUrl: app.baseUrl })
      .then((resp) => respond(res, resp, params))
      .catch((error) => handleError(res, error))
  })
}
