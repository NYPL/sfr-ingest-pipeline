const { MissingParamError } = require('../../lib/errors')
const { V3Edition } = require('../../lib/v3Edition')

const editionEndpoints = (app, respond, handleError) => {
  app.get('/sfr/edition', async (req, res) => {
    const params = req.query

    try {
      const editionRes = await fetchEdition(params, app)
      respond(res, editionRes, params, 'editionRecord')
    } catch (err) {
      handleError(res, err)
    }
  })

  app.post('/sfr/edition', async (req, res) => {
    const params = req.body
    try {
      const editionRes = await fetchEdition(params, app)
      respond(res, editionRes, params, 'editionRecord')
    } catch (err) {
      handleError(res, err)
    }
  })
}

const fetchEdition = (params, app) => {
  if (!('editionIdentifier' in params)) {
    throw new MissingParamError('Your request must include an identifier field or parameter')
  }

  const { editionIdentifier } = params

  const v3Edition = new V3Edition(app, editionIdentifier)
  return v3Edition.loadEdition()
}

module.exports = { fetchEdition, editionEndpoints }
