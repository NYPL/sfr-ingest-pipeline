function ElasticSearchError(message) {
  if (!message || typeof message !== 'string' || message.trim() === '') {
    throw new Error('error message is required')
  }

  this.message = message
  this.name = 'ElasticSearchError'
}

ElasticSearchError.prototype = Error.prototype

function MissingParamError(message) {
  if (!message || typeof message !== 'string' || message.trim() === '') {
    throw new Error('error message is required')
  }

  this.message = message
  this.name = 'MissingParamError'
}

MissingParamError.prototype = Error.prototype

function InvalidFilterError(message) {
  if (!message || typeof message !== 'string' || message.trim() === '') {
    throw new Error('error message is required')
  }

  this.message = message
  this.name = 'InvalidFilterError'
}

InvalidFilterError.prototype = Error.prototype

module.exports = {
  ElasticSearchError,
  MissingParamError,
  InvalidFilterError,
}
