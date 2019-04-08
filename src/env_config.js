import { parse } from 'dotenv'
import fs from 'fs'

/*
 * Selects the proper .env file defined on the command lind when this app was invoked
*/
exports.setEnv = () => {
  let env = process.env.NODE_ENV
  if (env === 'undefined') { env = 'development' }
  const envVars = parse(fs.readFileSync(`./config/${env}.env`))
  for (let k in envVars) {
      process.env[k] = envVars[k]
  }
}
