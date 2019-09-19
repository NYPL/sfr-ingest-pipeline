const Helpers = require('../helpers/esSourceHelpers')
const { DBConnection } = require('./db')

/** Class representing a search object. */
class V3Work {
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
    this.dbConn = new DBConnection(this.logger)
  }

  /**
   * Executes a search against the ElasticSearch index
   *
   * @returns {Promise} Promise object representing the result of the search request
   */
  parseWork(work, params) {
    let { recordType } = params
    if (!recordType) { recordType = 'editions' }
    const fetchObj = V3Work.getInstanceOrEditions(work)
    const dbWork = this.loadWork(fetchObj, recordType)

    return dbWork
  }

  async loadWork(work, recordType) {
    const dbWork = await this.getWork(work.uuid, ['measurements', 'subjects', 'agents', 'languages', 'alt_titles'])
    const identifiers = await this.getIdentifiers('work', dbWork.id)
    dbWork.identifiers = identifiers
    dbWork.instances = null
    dbWork.editions = null
    dbWork.edition_count = 0
    dbWork.edition_range = work.edition_range

    const getFunc = `get${recordType.slice(0, 1).toUpperCase()}${recordType.slice(1)}`
    const innerIds = new Set(work.instanceIds.map(ids => ids[`${recordType.slice(0, -1)}_id`]))
    dbWork[recordType] = await this[getFunc]([...innerIds])
    dbWork.edition_count = innerIds.size
    Helpers.parseAgents(dbWork, recordType)
    Helpers.parseLinks(dbWork, recordType)

    return dbWork
  }

  getWork(uuid, relatedTables) {
    return this.dbConn.loadWork(uuid, relatedTables)
  }

  getIdentifiers(table, identifier) {
    return this.dbConn.loadIdentifiers(table, identifier)
  }

  getEditions(editionIds) {
    return this.dbConn.loadEditions(editionIds, editionIds.length)
  }

  getInstances(instanceIds) {
    return this.dbConn.loadInstances(instanceIds, instanceIds.length)
  }

  static getInstanceOrEditions(work) {
    /* eslint-disable no-underscore-dangle */
    const dbRec = {
      uuid: work._id,
      edition_range: Helpers.formatSingleResponseEditionRange(work),
      instanceIds: [],
    }
    const instances = []
    if (work.inner_hits) {
      Object.values(work.inner_hits).forEach((match) => {
        match.hits.hits.forEach((inner) => {
          const instanceOffset = inner._nested.offset
          instances.push(work._source.instances[instanceOffset])
        })
      })
    } else {
      instances.push(...work._source.instances)
    }

    instances.forEach((inst) => {
      if ((inst.formats && inst.formats.length > 0)
      || inst.pub_date
      || (inst.agents && inst.agents.length > 0)
      || inst.pub_place) {
        dbRec.instanceIds.push({
          instance_id: inst.instance_id,
          edition_id: inst.edition_id,
        })
      }
    })

    return dbRec
    /* eslint-enable no-underscore-dangle */
  }
}

module.exports = { V3Work }
