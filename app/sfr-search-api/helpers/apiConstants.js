
/**
 * Work Table Joins
 * These relationships are loaded when an API request is received for a work detail
 * page
 *
 * Editions and instances are generally loaded through a separate query to avoid
 * overly large queries being made
 *
 * Possible values are: agents, alt_titles, dates, editions, instances, identifiers,
 * languages, links, measurements & subjects
 */
const workTableJoins = ['measurements', 'subjects', 'agents', 'languages', 'alt_titles']

/**
 * Instance Table Joins
 * Relationships to load for instance records, either in an Edition Detail request or
 * if the "recordType" is set to instance for Work Detail requests
 *
 * Possible values are: agents, alt_titles, dates, identifiers, items, languages, links
 * & measurements
 */
const instanceTableJoins = ['agents', 'items', 'languages', 'covers', 'dates', 'rights']

module.exports = {
  instanceTableJoins,
  workTableJoins,
}
