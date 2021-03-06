const bodybuilder = require('bodybuilder')
const Helpers = require('../../helpers/esSourceHelpers')
const { ElasticSearchError, MissingParamError } = require('../../lib/errors')

const workEndpoints = (app, respond, handleError) => {
  app.get('/sfr/work', async (req, res) => {
    const params = req.query

    try {
      const workRes = await fetchWork(params, app)
      respond(res, workRes, params)
    } catch (err) {
      handleError(res, err)
    }
  })

  app.post('/sfr/work', async (req, res) => {
    const params = req.body

    try {
      const workRes = await fetchWork(params, app)
      respond(res, workRes, params)
    } catch (err) {
      handleError(res, err)
    }
  })
}

const fetchWork = (params, app) => {
  if (!('identifier' in params)) {
    throw new MissingParamError('Your request must include an identifier field or parameter')
  }

  // TODO: Implement type-specific identifier matching
  // const { identifier, type } = params
  const { identifier } = params

  const body = bodybuilder()
    .orQuery('term', 'uuid', identifier)
    .orQuery('nested', { path: 'identifiers', query: { term: { 'identifiers.identifier': identifier } } })
    .orQuery('nested', { path: 'instances.identifiers', query: { term: { 'instances.identifiers.identifier': identifier } } })
    .orQuery('nested', { path: 'instances.items.identifiers', query: { term: { 'instances.items.identifiers.identifier': identifier } } })

  const esQuery = {
    index: process.env.ELASTICSEARCH_INDEX_V2,
    body: body.build(),
  }

  return new Promise((resolve, reject) => {
    app.client.search(esQuery)
      .then((resp) => {
        // Raise an error if 0 or many results were found
        const respCount = resp.hits.hits.length
        if (respCount < 1) reject(new ElasticSearchError('Could not locate a record with that identifier'))
        else if (respCount > 1) reject(new ElasticSearchError('Returned multiple records, identifier lacks specificity'))
        /* eslint-disable no-underscore-dangle */
        removeInvalidEditions(resp.hits.hits[0]._source)
        Helpers.formatResponseEditionRange(resp)
        resolve(resp.hits.hits[0]._source)
        /* eslint-enable no-underscore-dangle */
      })
      .catch(error => reject(error))
  })
}

const removeInvalidEditions = (source) => {
  // eslint-disable-next-line no-param-reassign
  source.instances = source.instances.filter(ed => (
    (ed.items && ed.items.length > 0)
      || ed.pub_date
      || (ed.agents && ed.agents.length > 0)
      || ed.pub_place
  ))
}

module.exports = { fetchWork, workEndpoints, removeInvalidEditions }
