const knex = require('knex')

class DBConnection {
  constructor(logger) {
    this.logger = logger
    this.pg = knex({
      client: 'pg',
      connection: process.env.DB_CONNECTION_STR,
    })
  }

  createSubQuery(originTable, targetTable, joinTable, tableFields) {
    const originTableID = this.pg.ref(`${originTable}.id`)
    return this.pg(targetTable)
      .join(joinTable, `${targetTable}.${joinTable.slice(0, -1)}_id`, `${joinTable}.id`)
      .where(`${targetTable}.${originTable.slice(0, -1)}_id`, originTableID)
      .select(this.pg.raw(DBConnection.buildAggString(tableFields, joinTable)))
      .as(joinTable)
  }

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

  static buildAggString(fields, label) {
    const formatedFields = []
    Object.keys(fields).forEach((field) => {
      formatedFields.push(`'${field}', ${fields[field]}`)
    })
    return `json_agg(json_build_object(${formatedFields.join(', ')})) AS ${label}`
  }

  async loadIdentifiers(table, identifier) {
    return this.pg(`${table}_identifiers`)
      .join('identifiers', `${table}_identifiers.identifier_id`, 'identifiers.id')
      .where(`${table}_identifiers.${table}_id`, identifier)
      .select('type', this.pg.raw('json_agg(identifiers.id) AS ids'))
      .groupBy('type')
      .then(async (rows) => {
        const recIds = []
        rows.forEach(async (row) => {
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
        })
        return recIds
      })
  }

  async loadInstances(instanceIds, limit) {
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
    const agentSub = this.createSubQuery('instances', 'agent_instances', 'agents', agentFields)

    const linkFields = {
      url: 'url',
      media_type: 'media_type',
      content: 'content',
      thumbnail: 'thumbnail',
      flags: 'flags',
    }
    const linkSub = this.createSubQuery('items', 'item_links', 'links', linkFields)

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

    return this.pg('instances')
      .whereIn('id', instanceIds)
      .select('*', agentSub, itemSub, langSub)
      .limit(limit)
      .then(rows => rows)
  }

  async loadEditions(editionIds, limit) {
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
    const agentSub = this.pg('agent_instances')
      .join('agents', 'agent_instances.agent_id', 'agents.id')
      .join('instances', 'agent_instances.instance_id', 'instances.id')
      .where('instances.edition_id', this.pg.ref('editions.id'))
      .select(this.pg.raw(DBConnection.buildAggString(agentFields, 'agents')))
      .as('agents')

    const linkFields = {
      url: 'url',
      media_type: 'media_type',
      content: 'content',
      thumbnail: 'thumbnail',
      flags: 'flags',
    }
    const linkSub = this.createSubQuery('items', 'item_links', 'links', linkFields)

    const itemFields = {
      source: 'source',
      content_type: 'content_type',
      modified: 'modified',
      drm: 'drm',
      links: `(${linkSub})`,
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
    const langSub = this.pg('instance_language')
      .join('language', 'instance_language.language_id', 'language.id')
      .join('instances', 'instance_language.instance_id', 'instances.id')
      .where('instances.edition_id', this.pg.ref('editions.id'))
      .select(this.pg.raw(DBConnection.buildAggString(langFields, 'languages')))
      .as('languages')

    return this.pg('editions')
      .whereIn('id', editionIds)
      .select('*', langSub, agentSub, itemSub)
      .limit(limit)
      .then(rows => rows)
  }
}

module.exports = { DBConnection };
