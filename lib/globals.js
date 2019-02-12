module.exports = function (app) {
    return Promise.all(promises).then((globals) => {
      app.globals = globals
      return app
    })
  }