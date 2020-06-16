/* eslint-disable prefer-destructuring */
const Helpers = require('../helpers/esSourceHelpers')
const { DBConnection } = require('./db')
const { NotFoundError } = require('./errors')

/** Class representing an edition record. */
class V3Edition {
  /**
   * Create a edition record.
   *
   * @param {Object} app Express object, contains various components needed for search.
   * @param {Integer} editionIdentifier Row id for edition in the postgres database.
   * @param {Boolean} showAll Control display of instances to either all(true) or only
   * those with items (false).
   */
  constructor(app, editionIdentifier, showAll) {
    this.app = app
    this.editionID = editionIdentifier
    this.showAll = showAll
    this.edition = null
    this.logger = this.app.logger
    this.dbConn = new DBConnection(this.logger, app.dbClient)
  }

  /**
   * Method to load and format an object containing edition metadata from the database
   *
   * @returns {object} Constructed edition record that can be sent to the end user
   */
  async loadEdition() {
    const editions = await this.getEditions()
    this.edition = editions[0]

    if (this.edition === undefined) {
      throw new NotFoundError(`No edition found matching identifier ${this.editionID}`)
    }

    // Transform source metadata into output format
    await this.parseEdition()

    // Transform source metadata from child records
    Helpers.parseAgents(this.edition, 'instances')
    Helpers.parseLinks(this.edition, 'instances')
    Helpers.parseDates(this.edition, 'instances')

    return this.edition
  }

  /**
   * Handler function for retrieving a set of editions specified by their internal
   * postgres row ids through the DBConnection class
   *
   * @param {array} editionIds Array of Row IDs to the editions table
   *
   * @returns {array} Array of edition objects from the database
   */
  getEditions() {
    return this.dbConn.loadEditions([this.editionID], 1)
  }

  /**
   * Handler function for retrieving a set of instances related to the current
   * edition record by the editions PostgreSQL row ID through the DBConnection class
   *
   * @returns {array} Array of instance objects from the database
   */
  getInstances() {
    return this.dbConn.getEditionInstances(this.editionID)
  }

  /**
   * Handler function to retrieve identifiers for a specified row through the
   * DBConnection class
   *
   * @param {string} table Name of the table to retrieve related identifiers. Should
   * generally be either works or instances (other option is items)
   * @param {integer} identifier Row ID in the specified table to retrieve identifiers for
   *
   * @returns {array} Array of identifier objects with id_type and identifier values
   */
  getIdentifiers(table, identifier) {
    return this.dbConn.loadIdentifiers(table, identifier)
  }

  /**
   * Method for performing some basic transformations of source metadata for presentation
   * to end users. This includes parsing dates, selecting the most appropriate title for
   * the edition and sorting the component instances.
   */
  async parseEdition() {
    this.edition.instances = await this.getInstances()

    // Select the publication year from the publication date range
    if (this.edition.publication_date) {
      this.edition.publication_date = this.edition.publication_date.match(/^\[([0-9]+)/)[1]
    }

    // Count all unique instance titles, sorting them into an object
    const titleCounts = this.edition.instances
      .map(i => i.title)
      .reduce((titles, title) => {
        // eslint-disable-next-line no-param-reassign
        titles[title] = (titles[title] || 0) + 1
        return titles
      }, {})

    // Select the most common instance title as the edition title
    this.edition.title = Object.keys(titleCounts)
      .sort((a, b) => titleCounts[b] - titleCounts[a])[0]

    // Assign sub_title from instance that title was drawn from
    const titleInsts = this.edition.instances
      .filter(i => i.title === this.edition.title && i.sub_title)
    this.edition.sub_title = titleInsts.length > 0 ? titleInsts[0].sub_title : null

    // If showAll is false, remove instances without items
    if (this.showAll === 'false') {
      this.edition.instances = this.edition.instances.filter(i => i.items !== null)
    }

    // Perform a custom sort on the instance array
    this.sortInstances()

    // Fetch Identifiers for instances
    await Promise.all(this.edition.instances.map(async (inst) => {
      // eslint-disable-next-line no-param-reassign
      inst.identifiers = await this.getIdentifiers('instance', inst.id)
    }))

    // Rename pub_place field in instances for consistency
    this.edition.instances.forEach((inst) => {
      // eslint-disable-next-line no-param-reassign
      inst.publication_place = inst.pub_place; delete inst.pub_place
    })

    // Remove items and covers from the edition; these are displayed on instances
    delete this.edition.items
    delete this.edition.covers
  }

  /**
   * Sort the component instances of this edition by the number of holdings, and
   * treating the "featured" instance (the instance in the edition card) as a special
   * case that should be placed first in the array
   */
  sortInstances() {
    // Sort instances by holdings
    // TODO sort() has changed in nodejs 11>, update this function to reflect that
    this.edition.instances.sort((a, b) => {
      const aHoldingCount = a.measurements.map(m => m.value).reduce((acc, cur) => acc + cur)
      const bHoldingCount = b.measurements.map(m => m.value).reduce((acc, cur) => acc + cur)
      return aHoldingCount < bHoldingCount
    })

    // Locate the featured instance by link URL if one is present
    if (this.edition.items) {
      // Get the featured instance links
      const editionLinks = [].concat(...this.edition.items.map(i => i.links.map(l => l.url)))

      // Filter the instance array to find the featured instance
      const featuredInst = this.edition.instances.filter((i) => {
        if (i.items) {
          const instanceLinks = [].concat(...i.items.map(t => t.links.map(l => l.url)))
          if (instanceLinks.filter(l => editionLinks.indexOf(l) > -1).length > 0) {
            return true
          }
        }
        return false
      })[0]

      // Splice out the featured instance and set the reordered array
      const featuredPos = this.edition.instances.indexOf(featuredInst)
      this.edition.instances.splice(featuredPos, 1)
      this.edition.instances = [featuredInst, ...this.edition.instances]
    }
  }
}

module.exports = { V3Edition }
