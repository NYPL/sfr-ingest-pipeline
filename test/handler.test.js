/* eslint-disable semi, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import Lambda from '../index.js'
import GitFetch from '../src/githubDataFetch.js'
import Kinesis from '../src/kinesisOutput.js'
import Helpers from '../src/fetchHelpers'
import event from '../event.json'
chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

describe('Handlers [index.js]', () => {
  describe('exports.handler', () => {
    let fetchStub, rdfStub, kinesisPut, getLCRels

    beforeEach(() => {
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
      let callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      expect(fetchStub).to.be.called
      expect(rdfStub).to.be.called
    })

    it('should fail if it failed to fetch any repository data', async () => {
      fetchStub.returns(false)
      let callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      const errArg = callback.firstCall.args[0]
      expect(errArg).to.be.instanceof(Error)
      expect(errArg.message).to.equal('Github API request returned too many 5XX errors')
    })

    it('should return 204 if the repository data it fetched is empty', async () => {
      fetchStub.returns([])
      let callback = sinon.spy()
      await Lambda.handler(event, null, callback)
      const msg = callback.firstCall.args[1]
      expect(msg).to.equal('No updated records found')
    })
  })

  describe('exports.retrieveRepos', () => {
    it('should call the getRepos function once', async () => {
      let repoFetchStub = sinon.stub(GitFetch, 'getRepos')
      repoFetchStub.resolves([['test001', '001']])
      await Lambda.retrieveRepos()
      expect(repoFetchStub).to.be.called
      repoFetchStub.restore()
    })
  })

  describe('exports.getRepoData', () => {
    it('should call the getRDF function once', async () => {
      let rdfFetchStub = sinon.stub(GitFetch, 'getRDF')
      await Lambda.getRepoData([{ 'data': 'stuff' }], [['list', 'item1', 'item2']])
      expect(rdfFetchStub).to.be.called
      rdfFetchStub.restore()
    })
  })
})
