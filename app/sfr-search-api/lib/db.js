
/**
 * This class manages connections and queries to the PostgreSQL database, which
 * serves as the "source of truth" for this project and which acts as the source
 * of final documents from the API. These methods control search and retrieval
 * within the database.
 */
class DBConnection {
  constructor(logger, dbClient) {
    this.logger = logger
    this.pg = dbClient
  }

  /**
   * This method is used to build complex queries by providing a template to create
   * a nested subquery which returns an array of aggregated JSON objects. This allows
   * queries against a single record to include multiple related values. For example, a
   * work query can include all agents in a single JSON array, simplifying the parsing
   * of results in the API
   *
   * @param {string} originTable Name of the table that this subquery will be made from
   * @param {string} targetTable Name of the table being joined directly. This is almost
   * always a relational, many-to-many table
   * @param {string} joinTable Name of the table ultimately being joined. This is
   * usually a table that contains a repeatable metadata element
   * @param {object} tableFields The fields to be returned from the joinTable. This is
   * an object of field names and values. These key/value pairs should usually be
   * symmetrical, unless the value is another subquery being made
   *
   * @returns {object} This returns a knex query object which can be combined into
   * a larger search object, or used to directly query the database
   */
  createSubQuery(originTable, targetTable, joinTable, tableFields) {
    const originTableID = this.pg.ref(`${originTable}.id`)
    return this.pg(targetTable)
      .join(joinTable, `${targetTable}.${joinTable.slice(0, -1)}_id`, `${joinTable}.id`)
      .where(`${targetTable}.${originTable.slice(0, -1)}_id`, originTableID)
      .select(this.pg.raw(DBConnection.buildAggString(tableFields, joinTable)))
      .as(joinTable)
  }

  createAggFromSelect(aggName, fields) {
    const formatedFields = []
    Object.keys(fields).forEach((field) => {
      formatedFields.push(`'${field}', ${fields[field]}`)
    })
    return this.pg.raw(`json_agg(json_build_object(${formatedFields.join(', ')})) FROM "${aggName}"`)
  }

  /**
   * This query looks up a work record in the database by UUID and returns that
   * record along with any specified related tables (agents, subjects, etc.). These
   * related tables are returned as arrays of JSON objects, which are automatically
   * parsed.
   *
   * @param {string} uuid The UUID of a work in the database
   * @param {array} relatedTables An array of related tables to return with the work record
   *
   * @returns {object} A work record retrieved from the database
   */
  loadWork(uuid, relatedTables) {
    const subQueries = []
    if (relatedTables.indexOf('agents') > -1) {
      const dateFields = {
        display_date: 'display_date',
        date_type: 'date_type',
      }
      const dateSub = this.createSubQuery('agents', 'agent_dates', 'dates', dateFields)

      const agentFields = {
        name: 'name',
        sort_name: 'sort_name',
        viaf: 'viaf',
        lcnaf: 'lcnaf',
        role: 'role',
        dates: `(${dateSub})`,
      }
      const agentSub = this.createSubQuery('works', 'agent_works', 'agents', agentFields)
      subQueries.push(agentSub)
    }

    if (relatedTables.indexOf('subjects') > -1) {
      const subjectFields = {
        subject: 'subject',
        authority: 'authority',
        uri: 'uri',
      }
      const subjectSub = this.createSubQuery('works', 'subject_works', 'subjects', subjectFields)
      subQueries.push(subjectSub)
    }

    if (relatedTables.indexOf('measurements') > -1) {
      const measurementFields = {
        quantity: 'quantity',
        value: 'value',
        weight: 'weight',
        taken_at: 'taken_at',
      }
      const measureSub = this.createSubQuery('works', 'work_measurements', 'measurements', measurementFields)
      subQueries.push(measureSub)
    }

    if (relatedTables.indexOf('languages') > -1) {
      const langFields = {
        language: 'language',
        iso_2: 'iso_2',
        iso_3: 'iso_3',
      }
      const langSub = this.pg('work_language')
        .join('language', 'work_language.language_id', 'language.id')
        .where('work_language.work_id', this.pg.ref('works.id'))
        .select(this.pg.raw(DBConnection.buildAggString(langFields, 'languages')))
        .as('languages')
      subQueries.push(langSub)
    }

    if (relatedTables.indexOf('alt_titles') > -1) {
      const altSub = this.pg('work_alt_titles')
        .join('alt_titles', 'work_alt_titles.title_id', 'alt_titles.id')
        .where('work_alt_titles.work_id', this.pg.ref('works.id'))
        .select(this.pg.raw('json_agg(title) AS alt_titles'))
        .as('alt_titles')
      subQueries.push(altSub)
    }

    return this.pg('works')
      .where({ uuid })
      .select('*', ...subQueries)
      .first()
  }

  /**
   * Used by the subQueryBuilder and other methods, this is a utility function
   * to create a JSON aggregation query in PostgreSQL.
   *
   * @param {object} fields An object containing the fields to return. The keys/values
   * should be identical expect in the case where a value is a nested subquery, in which
   * case it will be the text of that query
   * @param {string} label The label to apply to this value in the query, this is how
   * the aggregated results will be retrieved
   *
   * @returns {string} A formatted string to create a json_agg in postgres
   */
  static buildAggString(fields, label) {
    const formatedFields = []
    Object.keys(fields).forEach((field) => {
      formatedFields.push(`'${field}', ${fields[field]}`)
    })
    return `json_agg(json_build_object(${formatedFields.join(', ')})) AS ${label}`
  }

  /**
   * This loads an array of identifiers for the specified row in the specified table.
   * This does so by executing a set of queries against the identifiers table, first
   * creating an aggregated array of identifiers by type, and then retrieving the
   * identifier values for each type of identifiers
   *
   * @param {string} table The table for which to retrieve related identifiers
   * @param {integer} identifier The identifier to the row in the table for which
   * to retrieve identifiers
   *
   * @returns {array} An array of identifier objects each with the properties id_type
   * and identifier
   */
  async loadIdentifiers(table, identifier) {
    return this.pg(`${table}_identifiers`)
      .join('identifiers', `${table}_identifiers.identifier_id`, 'identifiers.id')
      .where(`${table}_identifiers.${table}_id`, identifier)
      .select('type', this.pg.raw('json_agg(identifiers.id) AS ids'))
      .groupBy('type')
      .then(async (rows) => {
        const recIds = []
        await Promise.all(rows.map(async (row) => {
          const realType = row.type || 'generic'
          const rowIds = await this.pg(realType)
            .whereIn('identifier_id', row.ids)
            .select('value')
            .then((values) => {
              const typeIds = []
              values.forEach((value) => {
                typeIds.push({
                  id_type: realType,
                  identifier: value.value,
                })
              })
              return typeIds
            })
          recIds.push(...rowIds)
        }))
        return recIds
      })
  }

  /**
   * This method is executed to return a set of instances related to a single work record.
   * The provided array of instance row IDs loads those specific instances and their
   * related tables. The limit parameter allows for returning a smaller number of results
   * for contexts such as search results where only a few will be displayed and retrieving
   * a full set of results will slow response times
   *
   * @param {array} instanceIds An array of instance row IDs to retrieve
   * @param {integer} limit The maximum number of instances to return
   * @param {array} joins An array of table names to select subqueries to execute
   *
   * @returns {object} A postgres response object that contains an array of identifiers
   */
  async loadInstances(instanceIds, limit, joins) {
    const agentFields = {
      name: 'name',
      sort_name: 'sort_name',
      viaf: 'viaf',
      lcnaf: 'lcnaf',
      role: 'role',
    }
    const agentSub = this.createSubQuery('instances', 'agent_instances', 'agents', agentFields)

    const linkFields = {
      url: 'url',
      media_type: 'media_type',
      content: 'content',
      thumbnail: 'thumbnail',
      flags: 'flags',
    }
    const linkSub = this.createSubQuery('items', 'item_links', 'links', linkFields)

    const rightsFields = {
      license: 'license',
      rights_statement: 'rights_statement',
    }
    const rightsSub = this.pg('rights')
      .join('instance_rights', 'instance_rights.rights_id', 'rights.id')
      .where('instance_rights.instance_id', this.pg.ref('instances.id'))
      .select(this.pg.raw(DBConnection.buildAggString(rightsFields, 'rights')))
      .as('rights')

    const itemFields = {
      source: 'source',
      content_type: 'content_type',
      modified: 'modified',
      drm: 'drm',
      links: `(${linkSub})`,
    }
    const itemSub = this.pg('items')
      .where('instance_id', this.pg.ref('instances.id'))
      .select(this.pg.raw(DBConnection.buildAggString(itemFields, 'items')))
      .as('items')

    const langFields = {
      language: 'language',
      iso_2: 'iso_2',
      iso_3: 'iso_3',
    }
    const langSub = this.pg('instance_language')
      .join('language', 'instance_language.language_id', 'language.id')
      .where('instance_language.instance_id', this.pg.ref('instances.id'))
      .select(this.pg.raw(DBConnection.buildAggString(langFields, 'languages')))
      .as('languages')

    const coverFields = {
      url: 'url',
      media_type: 'media_type',
      flags: 'flags',
    }
    const coverSub = this.pg('instance_links')
      .join('links', 'instance_links.link_id', 'links.id')
      .where('instance_links.instance_id', this.pg.ref('instances.id'))
      .where(this.pg.raw('CAST(flags ->> \'cover\' AS BOOLEAN) = true'))
      .select(this.pg.raw(DBConnection.buildAggString(coverFields, 'covers')))
      .as('covers')

    const dateFields = {
      display_date: 'display_date',
      date_type: 'date_type',
      date_range: 'date_range',
    }
    const dateSub = this.createSubQuery('instances', 'instance_dates', 'dates', dateFields)

    const measurementFields = {
      quantity: 'quantity',
      value: 'value',
    }
    const measureSub = this.createSubQuery('instances', 'instance_measurements', 'measurements', measurementFields)

    const subQueries = [
      { name: 'measurements', subquery: measureSub },
      { name: 'agents', subquery: agentSub },
      { name: 'items', subquery: itemSub },
      { name: 'languages', subquery: langSub },
      { name: 'covers', subquery: coverSub },
      { name: 'dates', subquery: dateSub },
      { name: 'rights', subquery: rightsSub },
    ]

    const selectQueries = joins
      ? subQueries.filter(a => joins.indexOf(a.name) > -1).map(a => a.subquery)
      : subQueries.map(a => a.subquery)

    const sortOrder = `array_position(ARRAY[${instanceIds.join(', ')}], id)`

    return this.pg('instances')
      .whereIn('id', instanceIds)
      .select('*', ...selectQueries)
      .orderBy(this.pg.raw(sortOrder))
      .limit(limit)
      .then(rows => rows)
  }

  /**
   * Similar to loadInstances this returns an array of edition records related to a
   * single work record. Related metadata records, such as agents and items, are loaded
   * through the editions related instances. Also similar is the limit, which returns
   * a subset of records for contexts in which a full set of records is unnecessary
   *
   * @param {array} editionIds An array of edition row IDs to retrieve
   * @param {integer} limit The maximum number of editions to return
   *
   * @returns {object} A postgres response object that contains an array of identifiers
   */
  async loadEditions(editionIds, limit) {
    const agentFields = {
      name: 'name',
      sort_name: 'sort_name',
      viaf: 'viaf',
      lcnaf: 'lcnaf',
      role: 'role',
    }
    const agentSub = this.pg.with('agentSub', (aq) => {
      aq.columns(agentFields).distinct()
        .from('agents', 'agent_instances.agent_id', 'agents.id')
        .join('agent_instances', 'agents.id', 'agent_instances.agent_id')
        .join('instances', 'agent_instances.instance_id', 'instances.id')
        .where('instances.edition_id', this.pg.ref('editions.id'))
    })
      .select(this.createAggFromSelect('agentSub', agentFields))
      .as('agents')

    const linkFields = {
      url: 'url',
      media_type: 'media_type',
      content: 'content',
      thumbnail: 'thumbnail',
      flags: 'flags',
    }
    const linkSub = this.createSubQuery('items', 'item_links', 'links', linkFields)

    const rightsFields = {
      license: 'license',
      rights_statement: 'rights_statement',
    }
    const rightsSub = this.pg('rights')
      .join('item_rights', 'item_rights.rights_id', 'rights.id')
      .where('item_rights.item_id', this.pg.ref('items.id'))
      .select(this.pg.raw(DBConnection.buildAggString(rightsFields, 'rights')))
      .as('rights')

    const itemFields = {
      source: 'source',
      content_type: 'content_type',
      modified: 'modified',
      drm: 'drm',
      links: `(${linkSub})`,
      rights: `(${rightsSub})`,
    }
    const itemSub = this.pg('items')
      .join('instances', 'items.instance_id', 'instances.id')
      .where('instances.edition_id', this.pg.ref('editions.id'))
      .select(this.pg.raw(DBConnection.buildAggString(itemFields, 'items')))
      .as('items')

    const langFields = {
      language: 'language',
      iso_2: 'iso_2',
      iso_3: 'iso_3',
    }
    const langSub = this.pg.with('distLang', (lq) => {
      lq.distinct(Object.values(langFields))
        .from('instance_language')
        .join('language', 'instance_language.language_id', 'language.id')
        .join('instances', 'instance_language.instance_id', 'instances.id')
        .where('instances.edition_id', this.pg.ref('editions.id'))
    })
      .select(this.createAggFromSelect('distLang', langFields))
      .as('languages')

    const coverFields = {
      url: 'url',
      media_type: 'media_type',
      flags: 'flags',
    }
    const coverSub = this.pg('instance_links')
      .join('links', 'instance_links.link_id', 'links.id')
      .join('instances', 'instance_links.instance_id', 'instances.id')
      .where('instances.edition_id', this.pg.ref('editions.id'))
      .where(this.pg.raw('CAST(flags ->> \'cover\' AS BOOLEAN) = true'))
      .select(this.pg.raw(DBConnection.buildAggString(coverFields, 'covers')))
      .as('covers')

    const sortOrder = `array_position(ARRAY[${editionIds.join(', ')}], id)`

    const workSub = this.pg('works')
      .where('works.id', this.pg.ref('editions.work_id'))
      .select('uuid')
      .as('work_uuid')

    return this.pg('editions')
      .whereIn('id', editionIds)
      .select('*', langSub, agentSub, itemSub, coverSub, workSub)
      .orderBy(this.pg.raw(sortOrder))
      .limit(limit)
      .then(rows => rows)
  }

  async getEditionInstances(editionID) {
    const instanceIDs = await this.pg('instances')
      .select('id')
      .where({ 'instances.edition_id': editionID })
      .then(rows => rows)

    return this.loadInstances(instanceIDs.map(i => i.id), instanceIDs.length)
  }
}

module.exports = { DBConnection };
