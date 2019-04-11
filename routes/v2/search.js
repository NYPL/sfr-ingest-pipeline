const bodybuilder = require('bodybuilder')
const { MissingParamError, ElasticSearchError } = require('../../lib/errors')

/**
 * 
 * @param {Object} app  
 * @param {*} respond 
 * @param {*} handleError 
 */
const searchEndpoints = (app, respond, handleError) => {
  app.post('/sfr/search', async (req, res) => {
    const params = req.body

    const searcher = new Search(app, params)
    let searchRes
    try {
      searcher.buildSearch()
      await searcher.addPaging()
      searchRes = await searcher.execSearch()
    } catch (err) {
      handleError(res, err)
    }

    respond(res, searchRes, params)
  })

  app.get('/sfr/search', async (rec, res) => {
    const params = rec.query

    const searcher = new Search(app, params)

    let searchRes
    try {
      searcher.buildSearch()
      await searcher.addPaging()
      searchRes = await searcher.execSearch()
    } catch (err) {
      handleError(res, err)
    }

    respond(res, searchRes, params)
  })
}

class Search {
  constructor(app, params) {
    this.app = app
    this.params = params
    this.logger = this.app.logger
  }

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
    } else if (fromPosition > 10000 && fromPosition < (this.total - 10000)) {
      this.logger.debug('SETTING DEEP SEARCH')
      const searchPoint = 10000
      const deepSearchAfter = await this.recursiveSearch(1000, fromPosition, searchPoint)
      this.query.rawOption('search_after', deepSearchAfter)
      this.query.from(0) // search_after essentially starts a new result set from zero
      this.query.size(perPage) // Reset page size after walking size override
      this.query.rawOption('_source', true) // Turn _source object back on for real result
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
    }
  }

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

  async getQueryCount() {
    const totalObj = await this.app.client.count({ body: this.queryCount })
    return totalObj.count
  }

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

  buildSearch() {
    if (!('field' in this.params) || !('query' in this.params)) {
      throw new MissingParamError('Your POST request must include either queries or filters')
    }

    const { field, query } = this.params

    this.query = bodybuilder()

    // Catch case where escape charaacter has been escaped and reduce to a single
    // escape character
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
      params.filters.map((filter) => {
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
