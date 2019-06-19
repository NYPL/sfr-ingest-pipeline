const bodybuilder = require('bodybuilder')
const { MissingParamError } = require('./errors')
const Helpers = require('../helpers/esSourceHelpers')

/*
 * Array of roles to exclude from author queries
 */
const blacklistRoles = ['arl', 'binder', 'binding designer', 'book designer',
  'book producer', 'bookseller', 'collector', 'consultant', 'contractor',
  'corrector', 'dedicatee', 'donor', 'copyright holder', 'court reporter',
  'electrotyper', 'engineer', 'engraver', 'expert', 'former owner', 'funder',
  'honoree', 'host institution', 'imprint', 'inscriber', 'other', 'patron',
  'performer', 'presenter', 'producer', 'production company', 'publisher',
  'printer', 'printer of plates', 'printmaker', 'proofreader',
  'publishing director', 'retager', 'secretary', 'sponsor', 'stereotyper',
  'thesis advisor', 'transcriber', 'typographer', 'woodcutter',
]

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
          Search.formatResponsePaging(resp)
          Search.formatResponseFacets(resp)
          Helpers.formatResponseEditionRange(resp)
          resolve(resp)
        })
        .catch(error => reject(error))
    })
  }

  /**
   * Adds sort arrays from the first and last search results to enable easy use
   * of the search_after ElasticSearch functionality for deep pagination.
   * The prev_page_sort and next_page_sort arrays can be passed as parameters
   * to retrieve the next or previous page.
   *
   * @param {Object} resp ElasticSearch search response object
   */
  static formatResponsePaging(resp) {
    if (resp.hits.hits.length) {
      const firstSort = resp.hits.hits[0].sort
      const lastSort = resp.hits.hits[resp.hits.hits.length - 1].sort
      // eslint-disable-next-line no-param-reassign
      resp.paging = {
        prev_page_sort: firstSort,
        next_page_sort: lastSort,
      }
    }
  }

  /**
   * Parses the aggregation object returned as part of the ElasticSearch
   * response into an object containing arrays of values for each facet. These
   * can be displayed used to help refine results. The format of the facets
   * object consists of a key that labels the facet with an array of
   * value/count pairs that display each value for the groupings along with the
   * total number of matching results in the full response object.
   *
   * @param {Object} resp ElasticSearch search response object
   */
  static formatResponseFacets(resp) {
    const facets = {}
    Object.keys(resp.aggregations).forEach((agg) => {
      const items = []
      const curAgg = resp.aggregations[agg]
      curAgg[agg].buckets.forEach((bucket) => {
        items.push({ value: bucket.key, count: bucket[agg].doc_count })
      })
      items.sort((a, b) => b.count - a.count)
      facets[agg] = items
    })
    /* eslint-disable no-param-reassign */
    resp.facets = facets
    delete resp.aggregations
    /* eslint-enable no-param-reassign */
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
    } else if (fromPosition < this.total && fromPosition > (this.total - 10000)) {
      this.logger.debug('SETTING FROM END SEARCH')
      this.invertSort()
      this.query.from(this.total - fromPosition)
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
   * @param {Object} searchAfter ElasticSearch search_after object used to retrieve next page.
   */
  async recursiveSearch(perPage, fromPosition, searchPoint, searchAfter = null) {
    const walkSize = (fromPosition - searchPoint < 1000) ? (fromPosition % 1000) : perPage
    const newSearchPoint = searchPoint + walkSize
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
      newAfter = await this.recursiveSearch(1000, fromPosition, newSearchPoint, newAfter)
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
            .orQuery('nested', {
              path: 'agents',
              query: {
                bool: {
                  must: {
                    query_string: { query: queryTerm, default_operator: 'and' },
                  },
                  must_not: {
                    terms: { 'agents.roles': blacklistRoles },
                  },
                },
              },
            })
            .orQuery('nested', {
              path: 'instances.agents',
              query: {
                bool: {
                  must: {
                    query_string: { query: queryTerm, default_operator: 'and' },
                  },
                  must_not: {
                    terms: { 'instances.agents.roles': blacklistRoles },
                  },
                },
              },
            })))
        break
      case 'lcnaf':
      case 'viaf':
        this.query.query('bool', b => b
          .query('bool', c => c
            // eslint-disable-next-line arrow-body-style
            .orQuery('nested', { path: 'agents' }, (q) => {
              return q.query('term', `agents.${field}`, queryTerm)
            })
            // eslint-disable-next-line arrow-body-style
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

    this.addFilters()
    this.addSort()
    this.addAggregations()
  }

  /**
   * Generates an array of sort options, allowing for a multifaceted set of
   * sorts. While generally only one sort option will be provided, this supports
   * an array of sorts to enable fine-grained sorting of results.
   *
   * Each object in the sort parameter should have a "field" and an (optional)
   * "dir" which can be set to ASC or DESC.
   */
  addSort() {
    if ('sort' in this.params && this.params.sort instanceof Array) {
      const sorts = []
      this.params.sort.forEach((sort) => {
        const { field, dir } = sort
        switch (field) {
          case 'title':
            sorts.push({ sort_title: dir || 'ASC' })
            break
          default:
            sorts.push({ [field]: dir || 'ASC' })
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
  }

  /**
   * Generates a filter block to create or a refine a search. Generally this
   * accepts a field from one of the search filter facets, but can be used
   * to generate a set of browse results as well.
   *
   * Due to the construction of the ElasticSearch documents, each filter must
   * be custom defined here to ensure proper discovery and refinement.
   */
  addFilters() {
    if ('filters' in this.params && this.params.filters instanceof Array) {
      // eslint-disable-next-line array-callback-return
      this.params.filters.map((filter) => {
        const { field, value } = filter
        switch (field) {
          case 'years':
            this.logger.debug(`Filtering works by years ${value.start} to ${value.end}`)
            // eslint-disable-next-line no-case-declarations
            const dateRange = {}
            if (value.start) { dateRange.gte = new Date(`${value.start}-01-01T12:00:00.000+00:00`) }
            if (value.end) { dateRange.lte = new Date(`${value.end}-12-31T12:00:00.000+00:00`) }
            this.query.query('nested', { path: 'instances', query: { range: { 'instances.pub_date': dateRange } } })
            break
          case 'language':
            this.logger.debug(`Filtering works by language ${value}`)
            this.query.query('bool', a => a
              .orQuery('nested', { path: 'language', query: { term: { 'language.language': value } } })
              .orQuery('nested', { path: 'instances.language', query: { term: { 'instances.language.language': value } } }))
            break
          default:
            this.logger.warning('API Not configured to handle this filter')
            break
        }
      })
    }
  }

  /**
   * Add aggregations to all search results. These are used to display filter
   * facets in the search result page and allow users to refine their searches
   *
   * Filters/facet display is all unfiform, but aggregation creation is
   * specific to each field and must be custom-defined within this method
   */
  addAggregations() {
    // Add aggregation for language facet
    const langFacet = 'language'
    this.query.agg('nested', { path: 'language' }, langFacet, a => a.agg('terms', 'language.language'))

    this.query.agg('nested', { path: 'instances.language' }, langFacet, a => a.agg('terms', 'instances.language.language', langFacet, b => b.agg('reverse_nested', {}, langFacet)))
  }
}

module.exports = { Search }
