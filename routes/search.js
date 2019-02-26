const config = require('config')
const bodybuilder = require('bodybuilder')

module.exports = function (app) {

  const respond = (res, _resp, params) => {
      var contentType = 'application/json'

      var resp = _resp
      if (contentType !== 'text/plain') resp = JSON.stringify(_resp, null, 2)

      app.logger.info('Search performed: ' + JSON.stringify(params))
      res.type(contentType)
      res.status(200).send(resp)
      return true
    }

  const handleError = (res, error) => {
    app.logger.error('Resources#handleError:', error)
    var statusCode = 500
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

  app.post(`/api/v0.1/sfr/works`, function (req, res) {
    var params = req.body

    let pageNum = (params.page) ? params.page : 0
    let perPage = (params.per_page) ? params.per_page : 10

    // This constructs the ES query document. Clauses are added to it below
    var body = bodybuilder()

    body.size(perPage)
    body.from(pageNum)

    if(!('queries' in params) && !('filters' in params)){
      handleError(res, {
        "name": "InvalidParameterError",
        "message": "Your POST request must include either queries or filters"
      })
    }

    // Query block, generally this will be where the main query against ES will be
    if ('queries' in params) {
      params["queries"].map((term) => {
        // Catch case where escape charaacter has been escaped and reduce to a single
        // escape character
        const queryTerm = term['value'].replace(/[\\]+([^\w\s]{1})/g, '\$1')
        switch(term['field']){
          case "author":
            body.query("query_string", {"fields": ["entities.name"], "query": queryTerm, "default_operator": "and"})
            break
          case "keyword":
            body.query("query_string", 'query', queryTerm, {"default_operator": "and"})
            break
          case "subject":
            body.query('query_string', {"fields": ["subjects.subject"], "query": queryTerm, "default_operator": "and"})
            break
          default:
            body.query('query_string', {"fields": [term["field"]], "query": queryTerm, "default_operator": "and"})
            break
        }
      })
    }

    // Filter block, used to search/filter data on specific terms. This can serve
    // as the main search field (useful for browsing) but generally it narrows
    // results in conjunction with a query
    if ('filters' in params) {
      params["filters"].map((filter) => {
        switch(filter['field']){
          case "year":
            body.filter("range", "instances.pub_date", filter['value'])
            break
          default:
            body.filter("term", filter['field'], filter['value'])
            break
        }
      })
    }

    // Sort block, this orders the results. Can be asc/desc and on any field
    if ('sort' in params) {
      params["sort"].map((sort) => {
        switch(sort["field"]){
          default:
            body.sort(sort['field'], sort['dir'])
        }
      })
    }

    // Aggregations block, this should be more complicated to enable full features
    // but essentially this builds an object of record counts grouped by a term
    // For example it can group works by authors/agents. This is used to
    // display browse options and do other metrics related querying
    if ('aggregations' in params) {
      params["aggregations"].map((agg) => {
        body.aggregation(agg['type'], agg['field'])
      })
    }
    // TODO: make the index an environment variable
    let esQuery = {
      index: 'sfr',
      body: body.build()
    }

    return app.client.search(esQuery, { baseUrl: app.baseUrl })
      .then((resp) => {
        respond(res, resp, params)
      })
      .catch((error) => handleError(res, error))
  })

  app.get(`/api/v0.1/sfr/works`, function (req, res) {
    var pageNum = (req.query.page) ? req.query.page : 1
    var perPage = (req.query.per_page) ? req.query.per_page : 10
    var userQuery = req.query.q
    var offset = (pageNum - 1) * perPage

    var body = bodybuilder()
      .query('query_string', 'query', userQuery)
      .size(perPage)
      .from(offset)
      .build()

    var params = {
      index: process.env.ELASTICSEARCH_INDEX,
      body: body
    }

    var filters = []
    var queryFields = []
    var fieldQuery = ''
    var filterQuery = {}
    if (req.query.filters) {
      filters = Object.keys(req.query.filters).map((prop) => {
          queryFields.push(prop)
          fieldQuery = req.query.filters[prop]
          var filterQuery = {
            fields: queryFields,
            query: fieldQuery
          }

        return filterQuery
      })

      params = {
        index: process.env.ELASTICSEARCH_INDEX,
        from: offset,
        size: perPage,
        body: {
          query: {
            query_string: {
              fields: queryFields,
              query: fieldQuery
            }
          }
        }
      }
    }

    return app.client.search(params, { baseUrl: app.baseUrl })
      .then((resp) => respond(res, resp, params))
      .catch((error) => handleError(res, error))
  })

}
