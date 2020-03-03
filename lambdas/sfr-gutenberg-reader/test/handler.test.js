/* eslint-disable no-unused-expressions, no-undef */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import Lambda from '../index'
import GitFetch from '../src/githubDataFetch'
import Kinesis from '../src/kinesisOutput'
import Helpers from '../src/fetchHelpers'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const { expect } = chai

describe('Handlers [index.js]', () => {
  describe('exports.handler', () => {
    let fetchStub
    let rdfStub
    let kinesisPut
    let getLCRels
    let event

    beforeEach(() => {
      event = JSON.stringify({
        source: 'local.test',
      })
      fetchStub = sinon.stub(Lambda, 'retrieveRepos')
      rdfStub = sinon.stub(Lambda, 'getRepoData')
      kinesisPut = sinon.stub(Kinesis, 'resultHandler')
      getLCRels = sinon.stub(Helpers, 'loadLCRels')
    })

    afterEach(() => {
      fetchStub.restore()
      rdfStub.restore()
      kinesisPut.restore()
      getLCRels.restore()
    })

    it('should call retrieveRepos and getRepoData function once', async () => {
      fetchStub.returns([['test001', '001']])
      const callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      expect(fetchStub).to.be.called
      expect(rdfStub).to.be.called
    })

    it('should fail if it failed to fetch any repository data', async () => {
      fetchStub.returns(false)
      const callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      const errArg = callback.firstCall.args[0]
      expect(errArg).to.be.instanceof(Error)
      expect(errArg.message).to.equal('Github API request returned too many 5XX errors')
    })

    it('should return 204 if the repository data it fetched is empty', async () => {
      fetchStub.returns([])
      const callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      const msg = callback.firstCall.args[1]
      expect(msg).to.equal('No updated records found')
    })

    it('should call loadSequentialRepos if local.bulk is specified', async () => {
      event = {
        source: 'local.bulk',
        repos: { start: 1, end: 2 },
      }
      const sequentialStub = sinon.stub(Lambda, 'loadSequentialRepos')
      sequentialStub.returns([['test001', '001']])
      const callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      expect(fetchStub).to.not.be.called
      expect(sequentialStub).to.be.called
      expect(rdfStub).to.be.called
      sequentialStub.restore()
    })
  })

  describe('exports.retrieveRepos', () => {
    it('should call the getRepos function once', async () => {
      const repoFetchStub = sinon.stub(GitFetch, 'getRepos')
      repoFetchStub.resolves([['test001', '001']])
      await Lambda.retrieveRepos()
      expect(repoFetchStub).to.be.called
      repoFetchStub.restore()
    })
  })

  describe('exports.getRepoData', () => {
    it('should call the getRDF function once', async () => {
      const rdfFetchStub = sinon.stub(GitFetch, 'getRDF')
      const addCoverStub = sinon.stub(GitFetch, 'addCoverFile')
      await Lambda.getRepoData([{ data: 'stuff' }], [['list', 'item1', 'item2']])
      expect(rdfFetchStub).to.be.called
      expect(addCoverStub).to.be.called
      rdfFetchStub.restore()
      addCoverStub.restore()
    })
  })

  describe('exports.loadSequentialRepos()', () => {
    it('should invoke getRepoRange until success returned', async () => {
      const loadRepoStub = sinon.stub(GitFetch, 'getRepoRange')
      loadRepoStub.onCall(0).returns(false)
      loadRepoStub.onCall(1).returns(false)
      loadRepoStub.onCall(2).returns(true)
      const success = await Lambda.loadSequentialRepos(1, 2)
      expect(success).to.be.true
      expect(loadRepoStub).to.be.calledThrice
      loadRepoStub.restore()
    })
  })
})
