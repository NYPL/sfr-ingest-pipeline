import csvtojson from 'csvtojson'

export const sleep = (ms, mult) => {
  return new Promise(resolve => setTimeout(resolve, ms * mult))
}

export const loadLCRels = () => {
  return new Promise((resolve, reject) => {
    let rels = []
    csvtojson().fromFile('./src/lc_relators.csv').then((obj) => {
      obj.forEach((rel) => {
        rels.push([rel['code'], rel['Label (English)'].toLowerCase()])
      })
      resolve(rels)
    }).catch((err) => {
      reject(err)
    })
  })
}
