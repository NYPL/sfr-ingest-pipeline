const bodybuilder = require('bodybuilder')
const { ElasticSearchError } = require('../../lib/errors')

/**
 * Handler function for utility endpoints. These will provide various supporting
 * services for the ResearchNow API, at present it provides a utility for viewing
 * all of the languages with works in the database.
 *
 * @param {Object} app Express application
 * @param {Function} respond Express response method
 * @param {Function} handleError Express error handler
 */
const utilEndpoints = (app, respond, handleError) => {
  /**
   * Language response utility. Responds with an array of existing languages. If
   * total exists as a query parameter, the total count of works for each language
   * will be returned.
   */
  app.get('/sfr/utils/languages', async (req, res) => {
    const params = req.query
    try {
      const langArray = await fetchLangs(app, params)
      const langRes = formatLanguageResponse(langArray)
      respond(res, langRes, params)
    } catch (err) {
      handleError(res, err)
    }
  })
}

/**
 * The main function that builds the language array query and returns the raw
 * ElasticSearch response. This uses the ES aggregations function to retrieve
 * a distinct array of languages in the database, with (optionally) counts of the
 * number of works associated with each language.
 *
 * @param {Object} app Express application
 * @param {Object} params Query parameters
 *
 * @returns {Object} The raw ElasticSearch response resolved by execQuery()
 */
const fetchLangs = (app, params) => {
  const { total } = params

  // Construct the ElasticSearch query using the BodyBuilder library
  const body = module.exports.buildQuery(total)

  // Create an object that can be understood by the ElasticSearch service
  const esQuery = {
    index: process.env.ELASTICSEARCH_INDEX_V2,
    body: body.build(), // Translates bodybuilder object into nested object
  }

  // Execute ElasticSearch query
  return module.exports.execQuery(app, esQuery, total)
}

/**
 * Utilizes BodyBuilder to created a nested query, which includes a "match_all" query
 * and an aggregation object with gathers all distinct languages (from the nested
 * fields associated with the instance records)
 *
 * @param {Boolean} total Toggle to control return of count of associated works with each language
 *
 * @returns {Object} A bodybuilder query object containing the language aggregation
 */
const buildQuery = (total) => {
  const body = bodybuilder()
  body.query('match_all', {})
  body.size(0)

  body.agg('nested', { path: 'instances.language' }, 'language_inner', (a) => {
    a.agg('terms', { field: 'instances.language.language', size: 250 }, 'unique_languages', (b) => {
      // If total is set, an additional aggregation is necessary to count the root works
      if (total) {
        b.agg('reverse_nested', {}, 'inner_count')
      }
      return b
    })
    return a
  })

  return body
}

/**
 * Executes an ElasticSearch query and returns the results. If no documents are
 * associated with the aggregation object an error occured. Otherwise the raw
 * ElasticSearch response is returned
 *
 * @param {Object} app Express application
 * @param {Object} esQuery Object containing ES index and built query object
 * @param {Boolean} total Toggle for the return of total works associated with each language
 */
const execQuery = (app, esQuery, total) => (
  new Promise((resolve, reject) => {
    app.client.search(esQuery)
      .then((resp) => {
        // Raise an error if no aggregations were returned
        const docCount = resp.aggregations.language_inner.doc_count
        if (docCount < 1) reject(new ElasticSearchError('Could not load language aggregations'))
        const langArray = module.exports.parseLanguageAgg(resp.aggregations.language_inner, total)
        resolve(langArray)
      })
      .catch(error => reject(error))
  }))

/**
 * Parses the aggregation received from ElasticSearch
 * @param {Object} mainAgg The root aggregation object received from ElasticSearch
 * @param {Boolean} total Toggle for the return of total works assocaited with each language
 *
 * @returns {Array} The array of unique languages with (optionally) the total works
 * associated with each
 */
const parseLanguageAgg = (mainAgg, total) => {
  const { buckets } = mainAgg.unique_languages
  return buckets.map((bucket) => {
    const lang = { language: bucket.key }
    if (total) { lang.count = bucket.inner_count.doc_count }
    return lang
  })
}

/**
 * Simple method for formatting array of unique languages as a response that can
 * returned to the user via the API
 *
 * @param {Array} langArr Formatted array of unique languages
 *
 * @returns {Object} Response object with standard status and data fields
 */
const formatLanguageResponse = langArr => (
  {
    status: 200,
    data: {
      languages: langArr,
    },
  }
)

module.exports = {
  utilEndpoints,
  fetchLangs,
  buildQuery,
  execQuery,
  parseLanguageAgg,
  formatLanguageResponse,
}
