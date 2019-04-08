/* eslint-disable semi, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import { resolve } from 'path'
import { Readable } from 'stream'
import fs from 'fs'
import AWS from 'aws-sdk-mock'

import AccessibilityChecker from '../src/accessibility_report.js'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

const JSON_BLOCK = require('./testReport.json')
const REPORT_JSON = ["", JSON_BLOCK]

describe('Accessibility Checker [accessibilityCheck.js]', () => {
  describe('runAccessibilityReport(url)', () => {
    let reportStub, tmpStub
    beforeEach(() => {
      reportStub = sinon.stub(AccessibilityChecker, 'parseReport')
      tmpStub = sinon.stub(AccessibilityChecker, 'downloadEpubFile')
    })

    afterEach(() => {
      reportStub.restore()
      tmpStub.restore()
    })

    after(() => {
      reportStub.restore()
      tmpStub.restore()
    })

    it('should generate a report', async () => {
      let report

      reportStub.returns({
        'aceVersion': '1.0.1',
        'score': 10,
        'violations': {
          'critical': 0,
          'serious': 3,
          'moderate': 69,
          'minor': 0
        },
        'json': {'some': 'json'}
      })
      tmpStub.resolves({ path: resolve('./test/testEpub.epub') })
      
      report = await AccessibilityChecker.runAccessibilityReport('fakeKey')
      
      expect(report).to.not.equal(null)
      expect(report['score']).to.equal(10)
      expect(report['aceVersion']).to.equal('1.0.1')
      expect(report).to.have.property('violations')
    }).timeout(60000)

    it('should return an error if it cannot create a tmp file', async () => {
      let report
      reportStub.returns({})
      tmpStub.throws("Could not create tmp file")

      try {
        report = await AccessibilityChecker.runAccessibilityReport('fakeKey')
      } catch(e) {
        expect(e).to.not.equal(null)
        expect(e.name).to.equal('Could not create tmp file')
      }
    })

    it('should return an error if it cannot generate a report', async () => {
      reportStub.returns({})
      tmpStub.returns(resolve('./test/nonExist.epub'))

      try {
        report = await AccessibilityChecker.runAccessibilityReport('fakeKey')
      } catch(e) {
        expect(e).to.not.equal(null)
      }
    })
  })

  
  describe('downloadEpubFile(key)', () => {
    let tmpStub
    beforeEach(() => {
      tmpStub = sinon.stub(AccessibilityChecker, 'createTmpFile')
    })

    afterEach(() => {
      tmpStub.restore()
    })

    it('should download and store an .epub file', async () => {
      AWS.mock('S3', 'getObject', Buffer.from(fs.readFileSync(resolve('./test/testEpub.epub'))))
      tmpStub.returns(fs.createWriteStream('./test_tmp.epub'))

      let fakeFile = await AccessibilityChecker.downloadEpubFile('fakeKey')
      
      expect(fakeFile.path).to.equal('./test_tmp.epub')
      fs.stat(fakeFile.path, false, (err) => {
        expect(err).to.equal(null)
        fs.unlink(fakeFile.path, (error) => {
          expect(error).to.equal(null)
        })
      })
      AWS.restore('S3', 'getObject')
    })

    it('should raise an error on missing file', async () => {
      const mockStream = new Readable({
        objectMode: true,
        read: function(size) {
          this.emit('error', 'pipe error')
        }
      })
      AWS.mock('S3', 'getObject', mockStream)
      tmpStub.returns(mockStream)
      try {
        await AccessibilityChecker.downloadEpubFile('fakeKey')
      } catch (e) {
        expect(e).to.not.equal(null)
      }
      AWS.restore('S3', 'getObject')
    })
  })

  describe('createTmpFile()', () => {
    it('should return a Writable object', () => {
      const tmpFile = AccessibilityChecker.createTmpFile()
      expect(tmpFile.path).to.match(/\/tmp\/[a-zA-Z0-9]+/)
      fs.stat(tmpFile.path, false, (err) => {
        expect(err).to.equal(null)
        fs.unlink(tmpFile.path, (error) => {
          expect(error).to.equal(null)
        })
      })
    })
  })
  
  describe('parseReport(report)', () => {
    it('should parseReport and return summary', () => {
      let summary = AccessibilityChecker.parseReport(REPORT_JSON)
      expect(summary).to.have.property('score')
      expect(summary['aceVersion']).to.equal('1.0.1')
      expect(summary['violations']).to.have.property('serious')
      expect(summary['violations']['moderate']).to.equal(69)
    })
  })

  describe('parseAssertions(assertions)', () => {
    let scoreStub, asserts

    beforeEach(() => {
      scoreStub = sinon.stub(AccessibilityChecker, 'calculateScore')
      asserts = [{
        'assertions': [
          {
            'earl:test': {
              'earl:impact': 'moderate'
            }
          }
        ]
      }]
    })

    afterEach(() => {
      scoreStub.restore()
    })

    it('should return a violation summary', () => {
      scoreStub.returns(6.6435)

      let scoreOut = AccessibilityChecker.parseAssertions(asserts)
      expect(scoreOut['score']).to.equal(6.6435)
      expect(scoreOut['violations']['moderate']).to.equal(1)
    })

    it('should return score of 0 if it\'s a negative number', () => {
      scoreStub.returns(-1)

      let scoreOut = AccessibilityChecker.parseAssertions(asserts)
      expect(scoreOut['score']).to.equal(0)
    })
  })

  describe('calculateScore(violations)', () => {
    it('should calculate score', () => {
      let violations = {
        critical: 0,
        serious: 3,
        moderate: 69,
        minor: 0
      }
      let score = AccessibilityChecker.calculateScore(violations)
      expect(score).to.equal(4.9375)
    })
  })
})
