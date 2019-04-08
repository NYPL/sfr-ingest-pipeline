/*
 * Selects the proper .env file defined on the command lind when this app was invoked
*/
exports.setEnv = () => {
    let env = process.env.NODE_ENV
    if(env === undefined){ env = 'development'}
    require('dotenv').config({path: `./config/${env}.env`})
}