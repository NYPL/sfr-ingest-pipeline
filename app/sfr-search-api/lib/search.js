const bodybuilder = require('bodybuilder')
const { MissingParamError, InvalidFilterError } = require('./errors')
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

const formatFilterTrans = {
  epub: 'application/epub+zip',
  pdf: 'application/pdf',
  html: 'text/html',
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

    this.show_all_works = false
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
          Search.filterSearchEditions(resp)
          resolve(resp)
        })
        .catch(error => reject(error))
    })
  }

  /**
   * Removes all but the top three most relevant instances/editions for each
   * returned work record.
   *
   * @param {Object} resp ElasticSearch search response object
   */
  static filterSearchEditions(resp) {
    resp.hits.hits.forEach((hit) => {
      /* eslint-disable no-param-reassign, no-underscore-dangle */
      let topInstances = []
      if (hit.inner_hits) {
        const innerSets = []
        Object.values(hit.inner_hits).forEach((match) => {
          const matchOffsets = new Set()
          match.hits.hits.forEach((inner) => {
            matchOffsets.add(inner._nested.offset)
          })
          innerSets.push(matchOffsets)
        })
        let instancePos = new Set()
        innerSets.forEach((set) => {
          if ([...instancePos].length === 0) {
            set.forEach(offset => instancePos.add(offset))
          } else {
            instancePos = new Set([...set].filter(x => instancePos.has(x)))
          }
        })
        instancePos.forEach((pos) => {
          topInstances.push(hit._source.instances[pos])
        })
        topInstances = Search.removeInvalidEditions(topInstances).slice(0, 3)
      } else {
        topInstances = hit._source.instances
          ? Search.removeInvalidEditions(hit._source.instances).slice(0, 3) : []
      }
      hit._source.edition_count = hit._source.instances
        ? Search.removeInvalidEditions(hit._source.instances).length : 0
      hit._source.instances = topInstances
      /* eslint-enable no-param-reassign, no-underscore-dangle */
    })
  }

  static removeInvalidEditions(editionList) {
    return editionList.filter(ed => (
      (ed.items && ed.items.length > 0)
        || ed.pub_date
        || (ed.agents && ed.agents.length > 0)
        || ed.pub_place
    ))
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
      const aggRoot = agg.slice(0, -2)
      const { buckets, lastLevel } = Search.getAggBottom(resp.aggregations[agg], aggRoot, 2)
      buckets.forEach((bucket) => {
        items.push({ value: bucket.key, count: bucket[lastLevel].doc_count })
      })
      items.sort((a, b) => b.count - a.count)
      facets[aggRoot] = items
    })
    /* eslint-disable no-param-reassign */
    resp.facets = facets
    delete resp.aggregations
    /* eslint-enable no-param-reassign */
  }

  /**
   * Recursively descend through an aggregation object to get the final set of
   * buckets that was the target of the original aggregation.
   *
   * @param {Object} agg Root aggregation object returned by ElasticSearch
   * @param {String} root Root name for the current aggregation
   * @param {Integer} pos Current position in the aggregation (levels from top)
   */
  static getAggBottom(agg, root, pos) {
    const aggKeys = Object.keys(agg)
    const aggLevel = `${root}_${pos}`
    if (aggKeys.indexOf(aggLevel) > -1) {
      const newPos = pos + 1
      return Search.getAggBottom(agg[aggLevel], root, newPos)
    }

    return { buckets: agg.buckets, lastLevel: aggLevel }
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

  buildSearch() {
    if (!('queries' in this.params) && !('query' in this.params && 'field' in this.params)) {
      throw new MissingParamError('Your POST request must include either a query object or an array of queries')
    }

    this.query = bodybuilder()

    if ('query' in this.params) {
      const { field, query } = this.params
      this.buildQuery(field, query)
    } else {
      const { queries } = this.params
      queries.forEach((q) => {
        const { field, query } = q
        this.buildQuery(field, query)
      })
    }

    this.queryCount = this.query.build()

    this.addFilters()
    this.addSort()
    this.addAggregations()
  }

  buildQuery(field, query) {
    if (!field || !query) {
      throw new MissingParamError('Each query object in your request must contain query and field fields')
    }

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
          case 'author':
            sorts.push({
              'agents.sort_name': {
                order: dir || 'ASC',
                nested: {
                  path: 'agents',
                  filter: { terms: { 'agents.roles': ['author'] } },
                  max_children: 1,
                },
              },
            })
            break
          case 'date':
            // eslint-disable-next-line no-case-declarations
            const sortField = dir === 'DESC' ? 'instances.pub_date_sort_desc' : 'instances.pub_date_sort'
            sorts.push({
              [sortField]: {
                order: dir || 'ASC',
                nested: {
                  path: 'instances',
                },
              },
            })
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
    let yearFilter = null
    let formatFilter = null
    this.formats = []
    let readFilter = ['nested', { path: 'instances.items', query: { exists: { field: 'instances.items.source' } } }]
    const langFilters = []
    if ('filters' in this.params && this.params.filters instanceof Array) {
      // eslint-disable-next-line array-callback-return
      this.params.filters.forEach((filter) => {
        const { field, value } = filter
        switch (field) {
          case 'years':
            if (!(typeof value === 'object')) {
              throw new InvalidFilterError('years filter value must be an object')
            } else if (!('start' in value || 'end' in value)) {
              throw new InvalidFilterError('years filter must contain a start or end value (or both)')
            } else if ((value.start === '' || value.start === undefined) && (value.end === '' || value.end === undefined)) {
              throw new InvalidFilterError('start or end field in years filter must contain a value')
            }
            Object.keys(value).forEach((key) => {
              const yearCheck = Number(value[key])
              // eslint-disable-next-line no-restricted-globals
              if (isNaN(yearCheck)) {
                throw new InvalidFilterError(`years filter ${key} value ${value[key]} is not a valid year`)
              } else if (yearCheck === 0) {
                delete value[key]
              } else {
                value[key] = yearCheck
              }
            })

            if (value.start && value.end) {
              if (value.end < value.start) {
                throw new InvalidFilterError(`end year ${value.end} must be greater than start year ${value.start}`)
              }
            }

            this.logger.debug(`Filtering works by years ${value.start} to ${value.end}`)
            // eslint-disable-next-line no-case-declarations
            const dateRange = {}
            if (value.start) { dateRange.gte = new Date(`${value.start}-01-01T00:00:00.000+00:00`) }
            if (value.end) { dateRange.lte = new Date(`${value.end}-12-31T24:00:00.000+00:00`) }
            dateRange.relation = 'WITHIN'
            yearFilter = ['range', 'instances.pub_date', dateRange]
            this.dateFilterRange = dateRange
            break
          case 'language':
            this.logger.debug(`Filtering works by language ${value}`)
            langFilters.push(['nested', { path: 'instances.language', query: { term: { 'instances.language.language': value } } }])
            break
          case 'show_all':
            if (!(typeof value === 'boolean')) {
              throw new InvalidFilterError('The show_all filter only accepts boolean values')
            }
            this.logger.debug('Disabling works return filter')
            if (value) {
              readFilter = null
              this.show_all_works = true
            }
            break
          case 'format':
            this.logger.debug(`Filtering works by format ${value}`)
            if (!(value in formatFilterTrans)) {
              this.logger.error(`Received invalid format filter value: ${value}`)
              throw new InvalidFilterError(`Format filter value (${value}) must be one of the following: pdf, epub or html`)
            }
            this.formats.push(formatFilterTrans[value])
            break
          default:
            this.logger.error('API Not configured to handle this filter')
            throw new InvalidFilterError(`${field} is not a valid filter option`)
        }
      })
    }

    if (this.formats.length > 0) {
      formatFilter = ['nested', { path: 'instances.items.links', query: { terms: { 'instances.items.links.media_type': this.formats } } }]
    }

    if (readFilter || yearFilter || formatFilter || langFilters.length > 0) {
      if (langFilters.length <= 1) {
        this.query.query('nested', { path: 'instances', inner_hits: { size: 100 } }, (q) => {
          Search.createFilterObject(q, yearFilter, readFilter, formatFilter, langFilters[0])
          return q
        })
      } else if (langFilters.length > 1) {
        this.query.query('bool', (q) => {
          this.innerSet = false
          this.setMultipleLangFilters(q, langFilters, formatFilter, yearFilter, readFilter)
          return q
        })
      }
    }
  }

  /**
   * Sets multiple filter groups when multiple languages are received. This allows
   * for multiple instances within each work to be matched when they contain a single
   * filtered language, rather than both. To do so all other instance filters must
   * be applied as well.
   *
   * To do so while maintaining the inner_hits setting, for instance level filtering,
   * this must insure that the setting is only applied to the first filter group, from
   * which it is reflected to all subsequent filter groups.
   *
   * @param {Object} parent BodyBuilder ElasticSearch queryObject
   * @param {Array} yearFilter Array of year filter options
   * @param {Array} readFilter Array of show_all filter options
   * @param {Array} formatFilter Array of format filter options
   * @param {Array} langFilters Array of language filters
   */
  setMultipleLangFilters(parent, langFilters, formatFilter, yearFilter, readFilter) {
    langFilters.forEach((filt) => {
      const nestedPath = { path: 'instances' }
      if (!this.innerSet) {
        nestedPath.inner_hits = { size: 100 }
        this.innerSet = true
      }
      parent.query('nested', nestedPath, (x) => {
        if (formatFilter || yearFilter || readFilter) {
          x.query('bool', (y) => {
            Search.createFilterObject(y, yearFilter, readFilter, formatFilter, filt)
            return y
          })
        } else {
          Search.createFilterObject(x, yearFilter, readFilter, formatFilter, filt)
        }
        return x
      })
    })
  }

  /**
   * This appends a single set of filter objects to the ElasticSearch query.
   * These filters are dependent on each other so must be added as a group, as
   * they are all nested within the instances array. Other filters, will not
   * be included in this group
   *
   * @param {Object} parent BodyBuilder ElasticSearch queryObject
   * @param {Array} yearFilt Array of year filter options
   * @param {Array} readFilt Array of show_all filter options
   * @param {Array} formatFilt Array of format filter options
   * @param {Array} langFilt Array of language filter options
   *
   * @returns {Object} Updated BodyBuilder query object
   */
  static createFilterObject(parent, yearFilt, readFilt, formatFilt, langFilt) {
    if (yearFilt) { parent.query(...yearFilt) }
    if (readFilt) { parent.query(...readFilt) }
    if (formatFilt) { parent.query(...formatFilt) }
    if (langFilt && langFilt.length > 0) { parent.query(...langFilt) }
    return parent
  }

  /**
   * Add aggregations to all search results. These are used to display filter
   * facets in the search result page and allow users to refine their searches
   *
   * Filters/facet display is all unfiform, but aggregation creation is
   * specific to each field and must be custom-defined within this method
   */
  addAggregations() {
    const aggs = []
    // Add aggregation for language facet
    aggs.push(Search.createLangAgg())

    aggs.forEach((agg) => {
      this.query.agg(...agg[0], (a) => {
        Search.createAgg(a, agg, 1)
        return a
      })
    })
  }

  /**
   * Appends a new nested layer to the current aggregation object
   *
   * @param {Array} aggArray Array of aggregation options
   * @param {Array} layer Options for the current aggregation being added
   * @param {Integer} pos Current count of aggregation options that have been added
   *
   * @returns {Integer} The increased position counter for the next layer
   */
  static addAggLayer(aggArray, layer, pos) {
    // eslint-disable-next-line no-param-reassign
    const newPos = pos + 1
    layer.push(`language_${newPos}`)
    aggArray.push(layer)
    return newPos
  }

  /**
   * Builds the aggregation object for the language facet. This includes optional
   * aggregation layers for the show_all_works option and the date range filter.
   * Future facets will potentially need to be aded as well as options
   *
   * @returns {Array} The array of aggregation layers to be transformed to an aggregation object
   */
  static createLangAgg() {
    // eslint-disable-next-line no-unused-vars
    let pos = 0
    const langAggOptions = []
    pos = Search.addAggLayer(langAggOptions, ['nested', { path: 'instances' }], pos)

    if (this.show_all_works) {
      pos = Search.addAggLayer(langAggOptions, ['nested', { path: 'instances.items' }], pos)
      pos = Search.addAggLayer(langAggOptions, ['filter', { exists: { field: 'instances.items.source' } }], pos)
      pos = Search.addAggLayer(langAggOptions, ['reverse_nested', { path: 'instances' }], pos)
    }

    if (this.dateFilterRange) {
      pos = Search.addAggLayer(langAggOptions, ['filter', { range: { 'instances.pub_date': this.dateFilterRange } }], pos)
    }

    if (this.formats && this.formats.length > 0) {
      pos = Search.addAggLayer(langAggOptions, ['nested', { path: 'instances.items.links' }], pos)
      pos = Search.addAggLayer(langAggOptions, ['filter', { terms: { 'instances.items.links.media_type': this.formats } }], pos)
      pos = Search.addAggLayer(langAggOptions, ['reverse_nested', { path: 'instances' }], pos)
    }

    pos = Search.addAggLayer(langAggOptions, ['nested', { path: 'instances.language' }], pos)
    pos = Search.addAggLayer(langAggOptions, ['terms', { field: 'instances.language.language', size: 200 }], pos)
    pos = Search.addAggLayer(langAggOptions, ['reverse_nested', {}], pos)

    return langAggOptions
  }

  /**
   * Converts an aggregation layer to a nested object within the aggregation object
   * @param {Object} query The parent query object
   * @param {Array} agg The current set of aggregation options for this layer
   * @param {Integer} pos The position of the current layer in the aggregations array
   */
  static createAgg(query, agg, pos) {
    if (!agg[pos]) { return null }
    const newPos = pos + 1
    return query.agg(...agg[pos], (sub) => {
      Search.createAgg(sub, agg, newPos)
      return sub
    })
  }
}

module.exports = { Search }
