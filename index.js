import express from 'express'
import compression from 'compression'
import bodyParser from 'body-parser'

import { router as generateRoute } from './src/routes/report_route.js'

const app = express(compression())
app.use(bodyParser.json({limit: '50mb'}))

app.use('/', generateRoute)

app.listen(3000, () => {
  console.log("Serving Ace Reports!")
})
