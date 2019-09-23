/* eslint-disable no-undef */
const chai = require('chai')
const sinon = require('sinon')
const sinonChai = require('sinon-chai')
const mockDB = require('mock-knex')

// Mock db connection
chai.should()
chai.use(sinonChai)
const { expect } = chai

const { DBConnection } = require('../lib/db')

describe('DBConnection manager tests', () => {
  describe('createSubQuery()', () => {
    let testDB
    beforeEach(() => {
      testDB = new DBConnection(sinon.mock())
    })

    afterEach(() => {
      // Nothing to do
    })

    it('should create a joined query for subqueries', (done) => {
      const newSubQuery = testDB.createSubQuery('testOrigins', 'testTarget', 'testJoins', { field1: 'field1', field2: 'field2' })
      const expectedOutput = 'select json_agg(json_build_object(\'field1\', field1, \'field2\', field2)) AS testJoins from "testTarget" inner join "testJoins" on "testTarget"."testJoin_id" = "testJoins"."id" where "testTarget"."testOrigin_id" = "testOrigins"."id"'
      expect(newSubQuery.toSQL().sql).to.equal(expectedOutput)
      done()
    })
  })

  describe('loadWork()', () => {
    let testDB
    const dbTracker = mockDB.getTracker()
    beforeEach(() => {
      testDB = new DBConnection(sinon.mock())
      dbTracker.install()
    })

    afterEach(() => {
      dbTracker.uninstall()
    })

    it('should make simple work query if no related tables specified', async () => {
      dbTracker.on('query', (query, step) => {
        [
          () => {
            expect(query.sql).to.equal('select * from "works" where "uuid" = $1 limit $2')
            query.response({
              id: 1,
              title: 'tester',
            })
          },
        ][step - 1]()
      })
      const dbWork = await testDB.loadWork('uuid', [])
      expect(dbWork.id).to.equal(1)
    })

    it('should make query with specified sub tables', async () => {
      dbTracker.on('query', (query, step) => {
        [
          () => {
            expect(query.sql).to.contain('alt_titles')
            expect(query.sql).to.contain('agent_works')
            query.response({
              id: 1,
              title: 'tester',
            })
          },
        ][step - 1]()
      })
      const dbWork = await testDB.loadWork('uuid', ['agents', 'alt_titles'])
      expect(dbWork.id).to.equal(1)
    })

    it('should make query with all subtables if specified', async () => {
      dbTracker.on('query', (query, step) => {
        [
          () => {
            expect(query.sql).to.contain('alt_titles')
            expect(query.sql).to.contain('agent_works')
            expect(query.sql).to.contain('subject_works')
            expect(query.sql).to.contain('work_measurements')
            expect(query.sql).to.contain('work_language')
            query.response({
              id: 1,
              title: 'tester',
            })
          },
        ][step - 1]()
      })
      const dbWork = await testDB.loadWork('uuid', ['agents', 'subjects', 'measurements', 'languages', 'alt_titles'])
      expect(dbWork.id).to.equal(1)
    })
  })

  describe('buildAggString', () => {
    it('should return built query string for aggregated json objects', (done) => {
      const testFields = {
        field1: 'field1',
        field2: 'field2',
        field3: 'alias',
      }

      const formattedStr = DBConnection.buildAggString(testFields, 'test')
      expect(formattedStr).to.equal('json_agg(json_build_object(\'field1\', field1, \'field2\', field2, \'field3\', alias)) AS test')
      done()
    })
  })
})
