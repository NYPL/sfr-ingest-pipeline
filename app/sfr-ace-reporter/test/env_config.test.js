import chai from 'chai'
import chaiAsPromised from 'chai-as-promised'
import sinonChai from 'sinon-chai'

import { loadEnv } from '../src/env_config.js'

chai.should()
chai.use(sinonChai)
chai.use(chaiAsPromised)
const expect = chai.expect

describe('Env Var Config [env_config.js]', () => {
  describe('setEnv()', () => {
    it('should load env from process.env.NODE_ENV', () => {
      loadEnv()
      expect(process.env.ENV).to.equal('test')
    })

    it('should default to development for env variables', () => {
      process.env.NODE_ENV = undefined
      loadEnv()
      expect(process.env.ENV).to.equal('development')
    })
  })
})
