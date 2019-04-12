import Search from '../../lib/search'

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

    const searcher = new Search(app, params)

    try {
      searcher.buildSearch()
      await searcher.addPaging()
      const searchRes = await searcher.execSearch()
      respond(res, searchRes, params)
    } catch (err) {
      handleError(res, err)
    }
  })

  app.get('/sfr/search', async (rec, res) => {
    const params = rec.query

    const searcher = new Search(app, params)

    try {
      searcher.buildSearch()
      await searcher.addPaging()
      const searchRes = await searcher.execSearch()
      respond(res, searchRes, params)
    } catch (err) {
      handleError(res, err)
    }
  })
}

module.exports = { searchEndpoints }
