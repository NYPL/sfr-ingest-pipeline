import express from 'express'
import AccessiblityRep from '../accessibility_report'

const router = express.Router()

router.post('/generate_report', (req, res) => {
  let bufData = Buffer.from(req.body.data)
  AccessiblityRep.runAccessibilityReport(bufData).then((reportData) => {
    let report = {
      'status': 200,
      'code': 'ace-success',
      'data': reportData
    }
    res.send(report)
  }).catch((err) => {
    let errReport = {
      'status': 500,
      'code': 'ace-error',
      'data': err
    }
    res.send(errReport)
  })
})

router.get('/', async (req, res) => {
  res.send({
    'status': 200,
    'code': 'service-up',
    'data': {
      'message': 'Report Service Running'
    }
  })
})

export { router }
