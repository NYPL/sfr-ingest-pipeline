/* eslint-disable no-param-reassign */
/**
 * Generates a year range for the publication dates of the editions associated
 * with a specific work.
 *
 * @param {Object} resp ElasticSearch response object
 */
const formatResponseEditionRange = (resp) => {
  resp.hits.hits.forEach((hit) => {
    const startYear = module.exports.getEditionRangeValue(hit, 'gte', 1)
    const endYear = module.exports.getEditionRangeValue(hit, 'lte', -1)

    let editionRange = ''
    if (startYear !== endYear) {
      editionRange = `${startYear} - ${endYear}`
    } else {
      editionRange = startYear
    }

    // eslint-disable-next-line no-param-reassign, no-underscore-dangle
    hit._source.edition_range = editionRange
  })
}

const formatSingleResponseEditionRange = (hit) => {
  const startYear = module.exports.getEditionRangeValue(hit, 'gte', 1)
  const endYear = module.exports.getEditionRangeValue(hit, 'lte', -1)

  let editionRange = ''
  if (startYear !== endYear) {
    editionRange = `${startYear} - ${endYear}`
  } else {
    editionRange = startYear
  }

  return editionRange
}

/**
 * Parses the provided Work object's editions for publication dates and returns
 * either the earliest or latest year. If not found, will return '???' for
 * display.
 *
 * @param {Object} hit Work object from the ElasticSearch response
 * @param {String} range Either 'lte' or 'gte' for the start or end of a range
 * @param {Number} flip Either 1 or -1 to flip the sorting to ASC or DESC.
 *
 * @returns {String} A 4-digit representation of the year found, else ????
 */
const getEditionRangeValue = (hit, range, flip) => {
  let year
  /* eslint-disable no-underscore-dangle */
  if (!hit._source.instances) { return '????' }
  const instanceSorter = hit._source.instances.map(o => ({ ...o }))
  const rangeInstance = instanceSorter.sort(
    module.exports.startEndCompare(range, flip),
  ).filter(instance => instance.pub_date)[0]
  if (rangeInstance) {
    year = new Date(`${rangeInstance.pub_date[range]}Z`).getUTCFullYear()
  } else {
    year = '????'
  }
  // eslint-disable-next-line no-restricted-globals
  if (isNaN(year)) { year = '????' }
  return year
  /* eslint-enable no-underscore-dangle */
}

/**
 * Generates a custom search function that can be customized to meet the needs
 * of the publication date fields. Handling cases when either the full date
 * is missing from an edition record or if one part of the date range is not
 * present.
 *
 * @param {String} startEnd Either 'lte' or 'gte' for the start and end of a range
 * @param {Number} sortFlip Either 1 or -1 to flip the sort order
 *
 * @returns {Function} dateComparison Function to be used by the sort method
 */
const startEndCompare = (startEnd, sortFlip) => {
  /**
   * Custom implementation of a sort method to handle different cases of publication
   * dates associated with edition records. The dates are appended with Noon GMT
   * to ensure that no timezone issues are encountered in retrieving the year.
   *
   * @param {Object} a Edition object for sorting
   * @param {Object} b Edition object for sorting
   *
   * @returns {Number} The sort order of the two objects, either -1, 0, or 1
   */
  const dateComparison = (a, b) => {
    if (!a.pub_date && !b.pub_date) return 0
    if (!a.pub_date) return -1 * sortFlip
    if (!b.pub_date) return 1 * sortFlip

    if (!a.pub_date[startEnd] && !b.pub_date[startEnd]) return 0
    if (!a.pub_date[startEnd]) return -1 * sortFlip
    if (!b.pub_date[startEnd]) return 1 * sortFlip

    const d1 = new Date(`${a.pub_date[startEnd]}Z`).getUTCFullYear()
    const d2 = new Date(`${b.pub_date[startEnd]}Z`).getUTCFullYear()

    if (d1 > d2) return 1 * sortFlip
    if (d1 < d2) return -1 * sortFlip
    return 0
  }
  return dateComparison
}

const parseAgents = (work, nestedType) => {
  const formatAgent = (agent) => {
    if (agent.dates) {
      agent.dates.forEach((date) => {
        // eslint-disable-next-line no-param-reassign
        agent[`${date.date_type}_display`] = date.display_date
      })
    }
    agent.roles = new Set([agent.role])
    delete agent.dates
    delete agent.role
    return agent
  }

  const groupAgents = (agents) => {
    const groupedAgents = []
    // eslint-disable-next-line no-plusplus
    for (let i = 0; i < agents.length; i++) {
      const existing = groupedAgents.find(findMatchingAgent, agents[i])
      if (existing) {
        existing.roles.add(agents[i].role)
      } else {
        groupedAgents.push(formatAgent(agents[i]))
      }
    }
    groupedAgents.forEach((agent) => {
      agent.roles = Array.from(agent.roles)
    })

    return groupedAgents
  }

  if (work.agents) {
    work.agents = groupAgents(work.agents)
  }
  work[nestedType].forEach((inner) => {
    if (inner.agents) {
      inner.agents = groupAgents(inner.agents)
    }
  })
}

const parseLinks = (work, nestedType) => {
  work[nestedType].forEach((inner) => {
    if (inner.items) {
      inner.items.forEach((item) => {
        if (!item.links) {
          inner.items.pop(item)
        } else {
          item.links.forEach((link) => {
            let flags
            try {
              flags = JSON.parse(link.flags)
            } catch (err) {
              // eslint-disable-next-line prefer-destructuring
              flags = link.flags
            }
            Object.keys(flags).forEach((key) => {
              link[key] = flags[key]
            })
            delete link.flags
          })
        }
      })
    }
  })
}

const parseDates = (work, nestedType) => {
  if (nestedType === 'editions') {
    const yearMatch = /^\[([0-9]+)/
    // eslint-disable-next-line no-plusplus
    for (let i = 0; i < work.editions.length; i++) {
      const dateRange = work.editions[i].publication_date
      // eslint-disable-next-line no-continue
      if (dateRange === null) continue
      const pubYear = dateRange.match(yearMatch)[1]
      work.editions[i].publication_date = pubYear
    }
  } else {
    // eslint-disable-next-line no-plusplus
    for (let i = 0; i < work.instances.length; i++) {
      if (work.instances[i].dates) {
        const pubDate = work.instances[i].dates.find(d => d.date_type === 'publication_date')
        if (pubDate) {
          work.instances[i].pub_date = pubDate.date_range
          work.instances[i].pub_date_display = pubDate.display_date
        }
        delete work.instances[i].dates
      }
    }
  }
}


function findMatchingAgent(element) {
  return element.name === this.name || element.viaf === this.viaf
}

module.exports = {
  formatResponseEditionRange,
  formatSingleResponseEditionRange,
  getEditionRangeValue,
  startEndCompare,
  parseAgents,
  parseLinks,
  parseDates,
}
