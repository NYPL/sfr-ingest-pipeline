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
   */
  constructor(app, editionIdentifier) {
    this.app = app
    this.editionID = editionIdentifier
    this.edition = null
    this.logger = this.app.logger
    this.dbConn = new DBConnection(this.logger, app.dbClient)
  }

  /**
   * Method to load and format an object containing work metadata from the database
   *
   * @param {object} work Parsed work object containing identifiers to be retrieved
   * @param {*} recordType Inner doc type to be included. Either instances or editions
   *
   * @returns {object} Constructed work record that can be sent to the end user
   */
  async loadEdition() {
    const editions = await this.getEditions()
    this.edition = editions[0]

    if (this.edition === undefined) {
      throw new NotFoundError(`No edition found matching identifier ${this.editionID}`)
    }

    await this.parseEdition()

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
   * Handler function for retrieving a set of instances specified by their internal
   * postgres row ids through the DBConnection class
   *
   * @param {array} editionIds Array of Row IDs to the instances table
   *
   * @returns {array} Array of instance objects from the database
   */
  getInstances() {
    return this.dbConn.getEditionInstances(this.editionID)
  }

  async parseEdition() {
    this.edition.instances = await this.getInstances()

    if (this.edition.publication_date) {
      this.edition.publication_date = this.edition.publication_date.match(/^\[([0-9]+)/)[1]
    }

    const titleCounts = this.edition.instances
      .map(i => i.title)
      .reduce((titles, title) => {
        const count = titles[title] || 0
        // eslint-disable-next-line no-param-reassign
        titles[title] = count + 1
        return titles
      }, {})

    this.edition.title = Object.keys(titleCounts)
      .sort((a, b) => titleCounts[b] - titleCounts[a])[0]

    this.sortInstances()
    delete this.edition.items
    delete this.edition.covers
  }

  sortInstances() {
    this.edition.instances.sort((a, b) => {
      const aHoldings = a.measurements.map(m => m.value)
      const bHoldings = b.measurements.map(m => m.value)
      return aHoldings.reduce((acc, cur) => acc + cur) < bHoldings.reduce((acc, cur) => acc + cur)
    })

    if (this.edition.items) {
      const editionLinks = [].concat(...this.edition.items.map(i => i.links.map(l => l.url)))
      const featuredInst = this.edition.instances.filter((i) => {
        if (i.items) {
          const instanceLinks = [].concat(...i.items.map(t => t.links.map(l => l.url)))
          if (instanceLinks.filter(l => editionLinks.indexOf(l) > -1).length > 0) {
            return true
          }
        }
        return false
      })
      const featuredPos = this.edition.instances.indexOf(featuredInst)
      this.edition.instances.splice(featuredPos, 1)
      this.edition.instances = [...featuredInst, ...this.edition.instances]
    }
  }
}

module.exports = { V3Edition }
