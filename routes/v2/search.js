const bodybuilder = require('bodybuilder')
const { MissingParamError } = require('../../lib/errors')

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

/** Class representing a search object. */
class Search {
  /**
   * Create a search object.
   *
   * @param {Object} app Express object, contains various components needed for search.
   * @param {Object} params Object containing search request from user.
   */
  constructor(app, params) {
    this.app = app
    this.params = params
    this.logger = this.app.logger
  }

  /**
   * Executes a search against the ElasticSearch index
   *
   * @returns {Promise} Promise object representing the result of the search request
   */
  execSearch() {
    const esQuery = {
      index: process.env.ELASTICSEARCH_INDEX_V2,
      body: this.query.build(),
    }

    return new Promise((resolve, reject) => {
      this.app.client.search(esQuery)
        .then((resp) => {
          if (this.reverseResult) resp.hits.hits.reverse()
          resolve(resp)
        })
        .catch(error => reject(error))
    })
  }

  /**
   * Adds paging parameters to the request body.
   *
   * @async
   */
  async addPaging() {
    this.logger.info('Adding paging information')
    const pageNum = (this.params.page) ? this.params.page : 0
    const perPage = (this.params.per_page) ? this.params.per_page : 10
    const prevSort = (this.params.prev_page_sort) ? this.params.prev_page_sort : null
    const nextSort = (this.params.next_page_sort) ? this.params.next_page_sort : null
    this.total = (this.params.total) ? this.params.total : await this.getQueryCount()
    const fromPosition = pageNum * perPage // ElasticSearch calculates from in raw count of records

    this.query.size(perPage)
    if (fromPosition < 10000 && !(prevSort || nextSort)) {
      this.logger.debug('SETTING STANDARD SEARCH')
      this.query.from(fromPosition)
    } else if (fromPosition < this.total && fromPosition > (this.total - 10000)) {
      this.logger.debug('SETTING FROM END SEARCH')
      this.invertSort()
      this.query.from(this.total - fromPosition)
      this.reverseResult = true
    } else if (nextSort) {
      this.logger.debug('SETTING NEXT PAGE SEARCH')
      this.query.rawOption('search_after', nextSort)
      this.query.from(0)
    } else if (prevSort) {
      this.logger.debug('SETTING PREVIOUS PAGE SEARCH')
      this.invertSort()
      this.query.rawOption('search_after', prevSort)
      this.query.from(0)
      this.reverseResult = true
    } else if (fromPosition > 10000 && fromPosition < (this.total - 10000)) {
      this.logger.debug('SETTING DEEP SEARCH')
      const searchPoint = 10000
      const deepSearchAfter = await this.recursiveSearch(1000, fromPosition, searchPoint)
      this.query.rawOption('search_after', deepSearchAfter)
      this.query.from(0) // search_after essentially starts a new result set from zero
      this.query.size(perPage) // Reset page size after walking size override
      this.query.rawOption('_source', true) // Turn _source object back on for real result
    }
  }

  /**
   * Recursively executes a search in ElasticSearch to retrieve deeply paged search requests. This
   * avoids the 10,000 record default search request depth on ElasticSearch indexes.
   *
   * @param {Number} perPage Number of results to include in iterative paging requests.
   * @param {Number} fromPosition Position/page in index to retrieve.
   * @param {Number} searchPoint Current position/page in the index.
   * @param {Object} searchAfter ElasticSearch search_after object used to retrieve next page in results.
   */
  async recursiveSearch(perPage, fromPosition, searchPoint, searchAfter = null) {
    const walkSize = (fromPosition - searchPoint < 1000) ? (fromPosition % 1000) : perPage
    searchPoint += walkSize
    this.logger.debug(`Pos: ${fromPosition}, Point: ${searchPoint}, Walk: ${walkSize}, After: ${searchAfter}`)
    if (searchAfter) {
      this.query.rawOption('search_after', searchAfter)
      this.query.rawOption('_source', false)
      this.query.from(0)
      this.query.size(walkSize)
    } else {
      this.query.from(10000 - perPage)
    }
    const searchRes = await this.execSearch()
    let newAfter = searchRes.hits.hits.slice(-1)[0].sort

    if (searchPoint < fromPosition) {
      newAfter = await this.recursiveSearch(1000, fromPosition, searchPoint, newAfter)
    }
    this.logger.debug(`Loading from ${searchPoint} (${searchAfter})`)
    return newAfter
  }

  /**
   * If the user does not provide the total number of records in their paging request, execute a
   * simple query to retrieve them. Utilizes the internal ElasticSearch index._count method.
   */
  async getQueryCount() {
    const totalObj = await this.app.client.count({ body: this.queryCount })
    return totalObj.count
  }

  /**
   * Invert the sort direction to enable fast retrieval of previous page results and queries
   * for pages from the end of the result set.
   */
  invertSort() {
    const newSort = []
    const tmpQuery = this.query.build()
    tmpQuery.sort.forEach((s) => {
      const field = Object.keys(s)[0]
      const newDir = (s[field].order === 'asc') ? 'desc' : 'asc'
      this.logger.debug(`SWITCH SORT ${newDir} ${field}`)
      newSort.push({ [field]: newDir })
    })
    this.query.sort(newSort)
  }

  /**
   * Create the main ElasticSearch query body utilizing the BodyBuilder library.
   * Creates the query, sort, filter, and aggregations
   */
  buildSearch() {
    if (!('field' in this.params) || !('query' in this.params)) {
      throw new MissingParamError('Your POST request must include either queries or filters')
    }

    const { field, query } = this.params

    this.query = bodybuilder()

    // Catch case where escape character has been escaped and reduce to a single escape character
    const queryTerm = query.replace(/[\\]+([^\w\s]{1})/g, '\\$1')

    switch (field) {
      case 'author':
        this.query.query('bool', b => b
          .query('bool', c => c
            .orQuery('nested', { path: 'agents', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
            .orQuery('nested', { path: 'instances.agents', query: { query_string: { query: queryTerm, default_operator: 'and' } } })))
        break
      case 'lcnaf':
      case 'viaf':
        this.query.query('bool', b => b
          .query('bool', c => c
            .orQuery('nested', { path: 'agents' }, (q) => {
              return q.query('term', `agents.${field}`, queryTerm)
            })
            .orQuery('nested', { path: 'instances.agents' }, (q) => {
              return q.query('term', `instances.agents.${field}`, queryTerm)
            })))
        break
      case 'subject':
        this.query.query('nested', { path: 'subjects', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
        break
      case 'title':
        this.query.query('query_string', { fields: ['title', 'alt_titles'], query: queryTerm, default_operator: 'and' })
        break
      case 'keyword':
      default:
        this.query.query('bool', b => b
          .query('bool', c => c
            .orQuery('query_string', 'query', queryTerm, { default_operator: 'and' })
            .orQuery('nested', { path: 'subjects', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
            .orQuery('nested', { path: 'agents', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
            .orQuery('nested', { path: 'instances', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
            .orQuery('nested', { path: 'instances.agents', query: { query_string: { query: queryTerm, default_operator: 'and' } } })
            .orQuery('nested', { path: 'instances.items', query: { query_string: { query: queryTerm, default_operator: 'and' } } })))
        break
    }
    this.queryCount = this.query.build()

    // Filter block, used to search/filter data on specific terms. This can serve
    // as the main search field (useful for browsing) but generally it narrows
    // results in conjunction with a query
    if ('filters' in this.params && this.params.filters instanceof Array) {
      // eslint-disable-next-line array-callback-return
      this.params.filters.map((filter) => {
        switch (filter.field) {
          case 'year':
            this.query.query('nested', { path: 'instances', query: { range: { 'instances.pub_date': { gte: filter.value, lte: filter.value } } } })
            break
          case 'language':
            this.query.query('nested', { path: 'language', query: { term: { 'language.language': filter.value } } })
            this.query.query('nested', { path: 'instances.language', query: { term: { 'instances.language.language': filter.value } } })
            break
          default:
            this.logger('Not configured to handle this filter, ignoring')
            break
        }
      })
    }

    // Sort block, this orders the results. Can be asc/desc and on any field
    if ('sort' in this.params && this.params.sort instanceof Array) {
      // eslint-disable-next-line array-callback-return
      const sorts = []
      this.params.sort.forEach((sort) => {
        const sortField = sort.field
        const { dir } = sort
        switch (field) {
          default:
            sorts.push({ [sortField]: dir })
        }
      })

      // Add a tiebreaker sort to ensure consistent paging
      sorts.push({ uuid: 'asc' })
      this.query.sort(sorts)
    } else {
      // Adding a default sort is necessary to enable deep pagination
      this.query.sort([
        { _score: 'desc' },
        { uuid: 'asc' },
      ])
    }

    // Aggregations block, this should be more complicated to enable full features
    // but essentially this builds an object of record counts grouped by a term
    // For example it can group works by authors/agents. This is used to
    // display browse options and do other metrics related querying
    if ('aggregations' in this.params && this.params.aggregations instanceof Array) {
      // eslint-disable-next-line array-callback-return
      this.params.aggregations.map((agg) => {
        this.query.aggregation(agg.type, agg.field)
      })
    }
  }
}

module.exports = { searchEndpoints }
