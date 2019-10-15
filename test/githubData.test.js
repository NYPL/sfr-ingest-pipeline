/* eslint-disable no-unused-expressions, no-undef */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import nock from 'nock'
import moment from 'moment'
import GithubFetch from '../src/githubDataFetch'
import RDFParser from '../src/parseRDF'
import { InstanceRecord } from '../src/sfrMetadataModel'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const { expect } = chai

describe('GitHub Data [githubDataFetch.js]', () => {
  describe('exports.getRepos()', () => {
    it('should return false in response to an invalid (non-200) response', async () => {
      nock('https://api.github.com')
        .post('/graphql')
        .reply(404, { message: 'Invalid Credentials' })

      const response = await GithubFetch.getRepos()
      expect(response).to.equal(false)
    })

    it('should return empty list for non-book, non-numbered repository', async () => {
      const badBook = {
        data: {
          organization: {
            repositories: {
              nodes: [{
                id: '',
                name: 'Gutenberg_Test',
                resourcePat: '/github/gitenberg',
                url: 'https://gutenberg.org/nan',
                pushedAt: moment().format(),
                __typename: 'Repository',
              }],
              __typename: 'Repositories',
            },
            __typename: 'Organization',
          },
        },
      }

      nock('https://api.github.com')
        .post('/graphql')
        .optionally(true)
        .reply(200, badBook)

      const response = await GithubFetch.getRepos()
      expect(response).to.deep.equal([])
    })

    it('should parse Valid response from Github API into list', async () => {
      const goodBook = {
        data: {
          organization: {
            repositories: {
              nodes: [{
                id: '0000',
                name: 'Test_Repo_0000',
                resourcePath: '/github/rel/path',
                url: 'https://gutenberg.org/0000',
                pushedAt: moment().format(),
                __typename: 'Repository',
              }],
              __typename: 'Repositories',
            },
            __typename: 'Organization',
          },
        },
      }
      nock('https://api.github.com')
        .post('/graphql')
        .optionally(true)
        .reply(200, goodBook)

      const responseTwo = await GithubFetch.getRepos()
      expect(responseTwo[0][1]).to.equal('0000')
      expect(responseTwo[0][0]).to.equal('Test_Repo_0000')
    })
  })

  describe('exports.getRDF()', () => {
    it('should return error message if repo request fails', async () => {
      nock('https://api.github.com')
        .post('/graphql')
        .reply(404, { message: 'Repository not found' })

      const repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse.status).to.equal(500)
      expect(repoResponse.recordID).to.equal('0000')
      expect(repoResponse.message).to.equal('Error in parsing Gutenberg Record')
    })

    it('should return data block parsed from RDF', async () => {
      const parseStub = sinon.stub(RDFParser, 'parseRDF').yields(null, {
        title: 'Hello',
        alt_titles: 'Test Data',
        entities: [],
        subjects: [],
      })
      const rdfData = {
        data: {
          repository: {
            object: {
              id: '1243w5436554',
              text: '<root><header>Hello</header><body>Test Data</body></root>',
              __typename: 'Object',
            },
            __typename: 'Repository',
          },
        },
      }

      nock('https://api.github.com')
        .post('/graphql')
        .reply(200, rdfData)

      const repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse.status).to.equal(200)
      expect(repoResponse.recordID).to.equal('0000')
      expect(repoResponse.message).to.equal('Retrieved Gutenberg Metadata')
      parseStub.restore()
    })

    it('should error if could not parse RDF file', async () => {
      const parseStub = sinon.stub(RDFParser, 'parseRDF').yields({
        message: 'Parsing Failed',
      })
      const rdfData = {
        data: {
          repository: {
            object: {
              id: '1243w5436554',
              text: '<>THIS ISN\'T A REAL RDF FILE<>',
              __typename: 'Object',
            },
            __typename: 'Repository',
          },
        },
      }

      nock('https://api.github.com')
        .post('/graphql')
        .reply(200, rdfData)

      const repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse.status).to.equal(500)
      expect(repoResponse.recordID).to.equal('0000')
      expect(repoResponse.message).to.equal('Could not parse Gutenberg Metadata')
      parseStub.restore()
    })
  })

  describe('addCoverFile()', () => {
    let getRepoStub
    let fetchCoverStub
    let testMetaRecord
    beforeEach(() => {
      getRepoStub = sinon.stub(GithubFetch, 'getMetadataFile')
      fetchCoverStub = sinon.stub(GithubFetch, 'fetchCoverFile')
      testMetaRecord = {
        data: {
          instances: [new InstanceRecord()],
        },
      }
    })

    afterEach(() => {
      getRepoStub.restore()
      fetchCoverStub.restore()
    })

    it('should not add link if no cover is found', async () => {
      getRepoStub.resolves({ field: 'testing' })
      await GithubFetch.addCoverFile(['test'], testMetaRecord)
      expect(testMetaRecord.data.instances[0].links.length).to.equal(0)
      expect(getRepoStub).to.be.calledOnceWith('test')
      expect(fetchCoverStub).to.be.not.called
    })

    it('should not add cover link if cover is marked "generated"', async () => {
      getRepoStub.resolves({ covers: [{ cover_type: 'generated', image_path: 'testing' }] })
      await GithubFetch.addCoverFile(['test'], testMetaRecord)
      expect(testMetaRecord.data.instances[0].links.length).to.equal(0)
      expect(getRepoStub).to.be.calledOnceWith('test')
      expect(fetchCoverStub).to.be.not.called
    })

    it('should add cover link if cover is marked "archival"', async () => {
      getRepoStub.resolves({
        covers: [{ cover_type: 'archival', image_path: 'testing' }],
        url: 'baseURL/',
      })
      fetchCoverStub.returns({
        url: 'coverURL',
        mediaType: 'image/tst',
        flags: { testing: true },
      })
      await GithubFetch.addCoverFile(['test'], testMetaRecord)
      expect(getRepoStub).to.be.calledOnceWith('test')
      expect(fetchCoverStub).to.be.calledOnceWith('baseURL/', 'testing')
      expect(testMetaRecord.data.instances[0].links.length).to.equal(1)
      expect(testMetaRecord.data.instances[0].links[0].url).to.equal('coverURL')
      expect(testMetaRecord.data.instances[0].links[0].flags.testing).to.be.true
    })
  })

  describe('getMetadataFile()', () => {
    it('should return parsed metadata.yaml data', async () => {
      const testMetadata = {
        data: {
          repository: {
            object: {
              text: 'testing: true',
            },
          },
        },
      }
      nock('https://api.github.com')
        .post('/graphql')
        .reply(200, testMetadata)

      const outMetadata = await GithubFetch.getMetadataFile('testRepo')
      expect(outMetadata.testing).to.be.true
    })

    it('should reject with an error if the API errors', async () => {
      nock('https://api.github.com')
        .post('/graphql')
        .reply(500, { message: 'test error' })
      let testErr
      try {
        await GithubFetch.getMetadataFile('testRepo')
      } catch (err) {
        testErr = err
      }
      expect(testErr.networkError.result.message).to.equal('test error')
    })
  })

  describe('fetchCoverFile()', () => {
    it('should return link fields for cover', (done) => {
      const testPath = 'test/ebooks'
      const testFile = 'covers/1234.png'

      const testLinkFields = GithubFetch.fetchCoverFile(testPath, testFile)
      expect(testLinkFields.url).to.equal('test/files/covers/1234.png')
      expect(testLinkFields.mediaType).to.equal('image/png')
      expect(testLinkFields.flags.cover).to.be.true
      expect(testLinkFields.flags.temporary).to.be.true
      done()
    })
  })

  describe('getRepoRange()', () => {
    let loadStub
    beforeEach(() => {
      loadStub = sinon.stub(GithubFetch, 'loadRepoPage')
    })

    afterEach(() => {
      loadStub.restore()
    })

    it('should return array of repository identifiers for current page', async () => {
      loadStub.onCall(0).returns(['repo1'])
      loadStub.onCall(1).returns(['repo2'])
      loadStub.onCall(2).returns(['repo3'])
      const testRepos = await GithubFetch.getRepoRange(0, 300)
      expect(loadStub).to.be.calledThrice
      expect(testRepos).to.deep.equal(['repo1', 'repo2', 'repo3'])
    })

    it('should call loadRepoPage with partial page for last page', async () => {
      loadStub.returns(['repo1'])
      const testRepos = await GithubFetch.getRepoRange(100, 25)
      expect(loadStub).to.be.calledOnceWith(1, 25)
      expect(testRepos[0]).to.equal('repo1')
    })

    it('should return false if unable to load repos from Github', async () => {
      loadStub.rejects()
      const testRepos = await GithubFetch.getRepoRange(0, 100)
      expect(testRepos).to.be.false
    })
  })

  describe('loadRepoPage()', () => {
    it('should resolve array of repo metadata for specified repos', async () => {
      const testData = [
        {
          name: 'xtest1',
          html_url: 'testURL1',
        }, {
          name: 'ytest2',
          html_url: 'testURL2',
        }, {
          name: 'ztest3',
          html_url: 'testURL3',
        },
      ]
      nock('https://api.github.com')
        .get((uri) => uri.includes('/users/GITenberg/repos'))
        .reply(200, testData)

      const testRepos = await GithubFetch.loadRepoPage(1, 3)
      expect(testRepos[0][0]).to.equal('xtest1')
      expect(testRepos[0][1]).to.equal('1')
      expect(testRepos[0][2]).to.equal('testURL1')
    })
    it('should resolve false if no repos are returned', async () => {
      const testData = []
      nock('https://api.github.com')
        .get((uri) => uri.includes('/users/GITenberg/repos'))
        .reply(200, testData)

      const testRepos = await GithubFetch.loadRepoPage(1, 3)
      expect(testRepos).to.be.false
    })

    it('should reject if Github API throws an error', async () => {
      nock('https://api.github.com')
        .get((uri) => uri.includes('/users/GITenberg/repos'))
        .reply(500, { message: 'test error' })
      let testErr
      try {
        await GithubFetch.loadRepoPage(1, 3)
      } catch (err) {
        testErr = err
      }
      expect(testErr.response.data.message).to.equal('test error')
    })
  })
})
