const bodybuilder = require('bodybuilder')
const { ElasticSearchError, MissingParamError } = require('../../lib/errors')

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
      const langRes = { languages: langArray }
      respond(res, langRes, params, 'languagesCount')
    } catch (err) {
      handleError(res, err)
    }
  })

  /**
   * Count response utility. Responds with counts of works, and if parameters are
   * supplied, counts of other record types from the database. Currently supported
   * are: instances, items, links and subjects
   */
  app.get('/sfr/utils/totals', async (req, res) => {
    const params = req.query
    try {
      const totalCounts = await fetchCounts(app, params)
      const totalRes = { counts: totalCounts }
      respond(res, totalRes, params, 'recordsCount')
    } catch (err) {
      handleError(res, err)
    }
  })
}

/**
 * The main function that builds the count utility. It relies on conducting a search
 * with a response size of zero(0) to quickly return a count of works in the index.
 * The params object can contain sub-documents to be counted as well
 *
 * @param {Object} app Express application
 * @param {Object} params Query parameters
 *
 * @returns {Object} A parsed count object containing only the requested data
 */
const fetchCounts = async (app, params) => {
  const body = bodybuilder()
  body.size(0)
  const nestedDict = {
    instances: 'instances',
    items: 'instances.items',
    links: 'instances.items.links',
    subjects: 'subjects',
  }
  Object.keys(params).forEach((key) => {
    if (!(key.toLowerCase() in nestedDict)) {
      throw new MissingParamError('This parameter is not a valid nested doctype')
    }
    if (params[key].toLowerCase() === 'true') {
      body.agg('nested', { path: nestedDict[key] }, `${key}_inner`)
    }
  })
  const esQuery = {
    index: process.env.ELASTICSEARCH_INDEX_V3,
    body: body.build(),
  }
  const docCounts = await module.exports.execQuery(app, esQuery)
  return module.exports.parseTotalCounts(docCounts)
}

/**
 * Parse the ElasticSearch response to extract the work count from the hits block,
 * and if other counts were requested, those counts from the aggregations block
 * This method also simplifies these keys for clearer responses
 *
 * @param {Object} counts An object containing work counts, and potentially others
 *
 * @returns {Object} A simplified version of the ElasticSearch response object
 */
const parseTotalCounts = (counts) => {
  const totals = {
    works: counts.hits.total,
  }
  if ('aggregations' in counts) {
    Object.keys(counts.aggregations).forEach((agg) => {
      const outKey = agg.replace('_inner', '')
      totals[outKey] = counts.aggregations[agg].doc_count
    })
  }

  return totals
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
const fetchLangs = async (app, params) => {
  const { total } = params

  // Construct the ElasticSearch query using the BodyBuilder library
  const body = module.exports.buildQuery(total)

  // Create an object that can be understood by the ElasticSearch service
  const esQuery = {
    index: process.env.ELASTICSEARCH_INDEX_V3,
    body: body.build(), // Translates bodybuilder object into nested object
  }

  // Execute ElasticSearch query
  const esResponse = await module.exports.execQuery(app, esQuery, total)
  // Raise an error if no aggregations were returned
  const docCount = esResponse.aggregations.language_inner.doc_count
  if (docCount < 1) throw new ElasticSearchError('Could not load language aggregations')
  return module.exports.parseLanguageAgg(esResponse.aggregations.language_inner, total)
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
 */
const execQuery = (app, esQuery) => (
  new Promise((resolve, reject) => {
    app.client.search(esQuery)
      .then((resp) => {
        resolve(resp)
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

module.exports = {
  utilEndpoints,
  fetchLangs,
  fetchCounts,
  buildQuery,
  execQuery,
  parseLanguageAgg,
  parseTotalCounts,
}
