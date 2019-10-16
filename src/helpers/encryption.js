import AWS from 'aws-sdk'

AWS.config.update({
  region: 'us-east-1',
  logger: process.stdout,
})

export default class VarDecryptor {
  constructor() {
    this.kms = new AWS.KMS()
  }

  async decryptVar(variable) {
    const decryptParams = {
      CiphertextBlob: Buffer.from(variable, 'base64'),
    }
    try {
      const decryptKey = await this.kms.decrypt(decryptParams).promise()
      return decryptKey.Plaintext.toString('utf-8')
    } catch (err) {
      return variable
    }
  }
}
