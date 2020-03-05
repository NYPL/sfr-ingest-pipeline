import csvtojson from 'csvtojson'
import logger from './helpers/logger'

exports.sleep = (ms, mult) => new Promise((resolve) => setTimeout(resolve, ms * mult))

exports.loadLCRels = async () => {
  try {
    const res = await exports.loadFromCSV()
    return res
  } catch (err) {
    logger.error('Unable to load LC Relations from CSV file')
    throw new Error('Unable to load LC Relations from CSV file')
  }
}

exports.loadFromCSV = () => new Promise((resolve, reject) => {
  const rels = []
  csvtojson().fromFile('./data/lc_relators.csv').then((obj) => {
    obj.forEach((rel) => {
      rels.push([rel.code, rel['Label (English)'].toLowerCase()])
    })
    resolve(rels)
  }).catch((err) => {
    reject(err)
  })
})
