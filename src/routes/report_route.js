import express from 'express'
import AccessiblityRep from '../accessibility_report'

const router = express.Router()

router.post('/generate_report', async (req, res) => {
  try {
    let bufData = Buffer.from(req.body.data)
    let reportData = await AccessiblityRep.runAccessibilityReport(bufData)
    let report = {
      'status': 200,
      'code': 'ace-success',
      'data': reportData
    }
    res.send(report)
  } catch(err) {
    let errReport = {
      'status': 500,
      'code': 'ace-error',
      'data': err
    }
  }
})

export { router }
