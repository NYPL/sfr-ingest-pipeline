const bodybuilder = require('bodybuilder')
const { ElasticSearchError } = require('../../lib/errors')

module.exports = (app, respond, handleError) => {

  app.get(`/sfr/work`, async (req, res) => {
    const params = req.query

    const workRes = await fetchWork(params, res)
    
    respond(res, workRes, params)
  })

  app.post('/sfr/work', async (req, res) => { 
    const params = req.body

    const searchRes = await fetchWork(params, res)

    respond(res, searchRes, params)
  })

  const fetchWork = (params, res) => {

    // TODO: Implement type-specific identifier matching
    const { identifier, type } = params
    
    const body = bodybuilder()
      .orQuery('term', 'uuid', identifier)
      .orQuery('nested', {path: "identifiers", query: {term: {"identifiers.identifier": identifier}}})
      .orQuery('nested', {path: "instances.identifiers", query: {term: {"instances.identifiers.identifier": identifier}}})
      .orQuery('nested', {path: "instances.items.identifiers", query: {term: {"instances.items.identifiers.identifier": identifier}}})

    const esQuery = {
      index: process.env.ELASTICSEARCH_INDEX,
      body: body.build()
    }
    
    return new Promise((resolve) => {
        app.client.search(esQuery)
            .then((resp) => {
                // Raise an error if 0 or many results were found
                const respCount = resp['hits']['hits'].length
                if (respCount < 1) return handleError(res, new ElasticSearchError('Could not locate a record with that identifier'))
                else if (respCount > 1) return handleError(res, new ElasticSearchError('Returned multiple records, identifier lacks specificity'))
                resolve(resp['hits']['hits'][0]['_source'])
            })
            .catch((error) => handleError(res, error))
    })
  }

}
