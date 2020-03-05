/* eslint-disable max-classes-per-file */
import yaml from 'js-yaml'

class LCSH {
  constructor(subject) {
    this.subject = subject
  }
}

const LCSHYamlType = new yaml.Type('!lcsh', {
  kind: 'scalar',

  resolve: (data) => typeof data === 'string',

  construct: (data) => new LCSH(data),

  instanceOf: LCSH,

  represent: (lcsh) => lcsh.subject,
})

class LCC {
  constructor(subject) {
    this.subject = subject
  }
}

const LCCYamlType = new yaml.Type('!lcc', {
  kind: 'scalar',

  resolve: (data) => typeof data === 'string',

  construct: (data) => new LCC(data),

  instanceOf: LCC,

  represent: (lcc) => lcc.subject,
})

module.exports = {
  LCSHYamlType,
  LCCYamlType,
}
