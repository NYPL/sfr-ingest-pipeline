const bodybuilder = require('bodybuilder')
const { ElasticSearchError, MissingParamError } = require('../../lib/errors')
const { V3Work } = require('../../lib/v3Work')

const workEndpoints = (app, respond, handleError) => {
  app.get('/sfr/work', async (req, res) => {
    const params = req.query
    try {
      const workRes = await fetchWork(params, app)
      respond(res, workRes, params, 'workRecord')
    } catch (err) {
      handleError(res, err)
    }
  })

  app.post('/sfr/work', async (req, res) => {
    const params = req.body
    try {
      const workRes = await fetchWork(params, app)
      respond(res, workRes, params, 'workRecord')
    } catch (err) {
      handleError(res, err)
    }
  })
}

const fetchWork = (params, app) => {
  if (!('identifier' in params)) {
    throw new MissingParamError('Your request must include an identifier field or parameter')
  }

  if (params.showAll && params.showAll !== 'true' && params.showAll !== 'false') {
    throw new MissingParamError('showAll must be set to either "true" or "false"')
  }

  // TODO: Implement type-specific identifier matching
  // const { identifier, type } = params
  const { identifier } = params

  const body = bodybuilder()
    .orQuery('term', 'uuid', identifier)
    .orQuery('nested', { path: 'identifiers', query: { term: { 'identifiers.identifier': identifier } } })
    .orQuery('nested', { path: 'instances.identifiers', query: { term: { 'instances.identifiers.identifier': identifier } } })

  const esQuery = {
    index: process.env.ELASTICSEARCH_INDEX_V3,
    body: body.build(),
  }

  return new Promise((resolve, reject) => {
    app.client.search(esQuery)
      .then((resp) => {
        // Raise an error if 0 or many results were found
        const respCount = resp.hits.hits.length
        if (respCount < 1) reject(new ElasticSearchError('Could not locate a record with that identifier'))
        else if (respCount > 1) reject(new ElasticSearchError('Returned multiple records, identifier lacks specificity'))
        const v3Work = new V3Work(app, params)
        resolve(v3Work.parseWork(resp.hits.hits[0], params))
      })
      .catch(error => reject(error))
  })
}

module.exports = { fetchWork, workEndpoints }
