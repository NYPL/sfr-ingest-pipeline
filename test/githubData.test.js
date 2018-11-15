/* eslint-disable semi, no-unused-expressions */
import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinon from 'sinon'
import sinonChai from 'sinon-chai'
import nock from 'nock'
import moment from 'moment'
import GithubFetch from '../src/githubDataFetch.js'
import RDFParser from '../src/parseRDF.js'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

describe('GitHub Data [githubDataFetch.js]', () => {
  describe('exports.getRepos()', () => {
    it('should return false in response to an invalid (non-200) response', async () => {
      let gitErrStub = nock('https://api.github.com')
        .post('/graphql')
        .reply(404, { 'message': 'Invalid Credentials' })

      let response = await GithubFetch.getRepos()
      expect(response).to.equal(false)
    })

    it('should return empty list for non-book, non-numbered repository', async () => {
      let badBook = {
        'data': {
          'organization': {
            'repositories': {
              'nodes': [{
                'id': '',
                'name': 'Gutenberg_Test',
                'resourcePath': '/github/gitenberg',
                'url': 'https://gutenberg.org/nan',
                'updatedAt': moment().format(),
                '__typename': 'Repository'
              }],
              '__typename': 'Repositories'
            },
            '__typename': 'Organization'
          }
        }
      }

      let badGitStub = nock('https://api.github.com')
        .post('/graphql')
        .optionally(true)
        .reply(200, badBook)

      let response = await GithubFetch.getRepos()
      expect(response).to.deep.equal([])
    })

    it('should parse Valid response from Github API into list', async () => {
      let goodBook = {
        'data': {
          'organization': {
            'repositories': {
              'nodes': [{
                'id': '0000',
                'name': 'Test_Repo_0000',
                'resourcePath': '/github/rel/path',
                'url': 'https://gutenberg.org/0000',
                'updatedAt': moment().format(),
                '__typename': 'Repository'
              }],
              '__typename': 'Repositories'
            },
            '__typename': 'Organization'
          }
        }
      }
      let gitStub = nock('https://api.github.com')
        .post('/graphql')
        .optionally(true)
        .reply(200, goodBook)

      let responseTwo = await GithubFetch.getRepos()
      expect(responseTwo[0][1]).to.equal('0000')
      expect(responseTwo[0][0]).to.equal('Test_Repo_0000')
    })
  })

  describe('exports.getRDF()', () => {
    it('should return error message if repo request fails', async () => {
      let gitErrStub = nock('https://api.github.com')
        .post('/graphql')
        .reply(404, { 'message': 'Repository not found' })

      let repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse['status']).to.equal(500)
      expect(repoResponse['gutenbergID']).to.equal('0000')
      expect(repoResponse['message']).to.equal('Error in parsing Gutenberg Record')
    })

    it('should return data block parsed from RDF', async () => {
      let parseStub = sinon.stub(RDFParser, 'parseRDF').yields(null, {
        'title': 'Hello',
        'altTitle': 'Test Data',
        'entities': [],
        'subjects': []
      })
      let rdfData = {
        'data': {
          'repository': {
            'object': {
              'id': '1243w5436554',
              'text': '<root><header>Hello</header><body>Test Data</body></root>',
              '__typename': 'Object'
            },
            '__typename': 'Repository'
          }
        }
      }

      let gitErrStub = nock('https://api.github.com')
        .post('/graphql')
        .reply(200, rdfData)

      let repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse['status']).to.equal(200)
      expect(repoResponse['gutenbergID']).to.equal('0000')
      expect(repoResponse['message']).to.equal('Retrieved Gutenberg Metadata')
      parseStub.restore()
    })

    it('should error if could not parse RDF file', async () => {
      let parseStub = sinon.stub(RDFParser, 'parseRDF').yields({
        'message': 'Parsing Failed'
      })
      let rdfData = {
        'data': {
          'repository': {
            'object': {
              'id': '1243w5436554',
              'text': '<>THIS ISN\'T A REAL RDF FILE<>',
              '__typename': 'Object'
            },
            '__typename': 'Repository'
          }
        }
      }

      let gitErrStub = nock('https://api.github.com')
        .post('/graphql')
        .reply(200, rdfData)

      let repoResponse = await GithubFetch.getRDF(['Test_Repo_0000', '0000'], [['aut', 'author']])
      expect(repoResponse['status']).to.equal(500)
      expect(repoResponse['gutenbergID']).to.equal('0000')
      expect(repoResponse['message']).to.equal('Could not parse Gutenberg Metadata')
      parseStub.restore()
    })
  })
})
