import csvtojson from 'csvtojson'
import logger from './helpers/logger'

exports.sleep = (ms, mult) => {
  return new Promise(resolve => setTimeout(resolve, ms * mult))
}

exports.loadLCRels = async () => {
  try {
    let res = await exports.loadFromCSV()
    return res
  } catch (err) {
    logger.error('Unable to load LC Relations from CSV file')
    throw new Error('Unable to load LC Relations from CSV file')
  }
}

exports.loadFromCSV = () => {
  return new Promise((resolve, reject) => {
    let rels = []
    csvtojson().fromFile('./data/lc_relators.csv').then((obj) => {
      obj.forEach((rel) => {
        rels.push([rel['code'], rel['Label (English)'].toLowerCase()])
      })
      resolve(rels)
    }).catch((err) => {
      reject(err)
    })
  })
}
