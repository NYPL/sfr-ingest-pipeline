const { V3Search } = require('../../lib/v3Search')

/**
 * Constructs the simple search endpoints for GET/POST requests. Invokes the search
 * object to construct a query and execute it.
 *
 * @param {Object} app The express application, used to construct endpoints
 * @param {Response} respond Function that responds to the API request
 * @param {ErrorResponse} handleError Function that responds with non-200 Status Code
 */

const searchEndpoints = (app, respond, handleError) => {
  app.post('/sfr/search', async (req, res) => {
    const params = req.body

    const searcher = new V3Search(app, params)

    try {
      searcher.buildSearch()
      await searcher.addPaging()
      const searchRes = await searcher.execSearch()
      respond(res, searchRes, params, 'searchResults')
    } catch (err) {
      let errReason
      let errType
      try {
        errReason = err.body.response.error.failed_shards[0].reason.caused_by.reason
        errType = err.body.response.error.failed_shards[0].reason.caused_by.type
      } catch (innerErr) {
        // Unable to find specific error type or reason. pass
      }
      handleError(res, err, errType, errReason)
    }
  })

  app.get('/sfr/search', async (rec, res) => {
    const params = {}

    // Handle any JSON parts of the query
    Object.keys(rec.query).forEach((key) => {
      try {
        params[key] = JSON.parse(rec.query[key])
      } catch (err) {
        params[key] = rec.query[key] // Not a JSON field, just add value to params
      }
    })

    const searcher = new V3Search(app, params)

    try {
      searcher.buildSearch()
      await searcher.addPaging()
      const searchRes = await searcher.execSearch()
      respond(res, searchRes, params, 'searchResults')
    } catch (err) {
      let errReason
      let errType
      try {
        const errResp = JSON.parse(err.response)
        errReason = errResp.error.failed_shards[0].reason.caused_by.reason
        errType = errResp.error.failed_shards[0].reason.caused_by.type
      } catch (jsonErr) {
        // Unable to parse json error
      }
      handleError(res, err, errType, errReason)
    }
  })
}

module.exports = { searchEndpoints }
