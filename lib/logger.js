const { createLogger, format, transports } = require('winston')

const logLevel = (process.env.NODE_ENV === 'production') ? 'info' : 'debug'

const getLogLevelCode = (levelString) => {
  switch (levelString) {
    case 'emergency':
      return 0
    case 'alert':
      return 1
    case 'critical':
      return 2
    case 'error':
      return 3
    case 'warning':
      return 4
    case 'notice':
      return 5
    case 'info':
      return 6
    case 'debug':
      return 7
    default:
      return 'n/a'
  }
}

const nyplLogFormat = format((info, opts) => {
  info.levelCode = getLogLevelCode(info.level)
  info.timestamp = new Date().toISOString()

  return info
})

let loggerTransports = [
  new transports.File({
    level: logLevel,
    filename: './log/discovery-api.log',
    handleExceptions: true,
    maxsize: 5242880, // 5MB
    maxFiles: 5,
    colorize: false,
    json: false
  })
]

// spewing logs while running tests is annoying
if (process.env.NODE_ENV !== 'test') {
  loggerTransports.push(new transports.Console({
    // level: logLevel,
    handleExceptions: true,
    json: true,
    colorize: false
  }))
}

const logger = createLogger({
  format: format.combine(
    nyplLogFormat(),
    format.json()
  ),
  transports: loggerTransports,
  exitOnError: false
})

module.exports = logger
