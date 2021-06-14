const AWS = require('aws-sdk');
const s3 = new AWS.S3();

class ImageUpload {
  constructor(s3) {
    this.s3 = s3;
  }

  /**
   * @param{string} imageBase64
   * @returns {Promise<void>}
   */
  async uploadToBucket(imageBase64) {
    let buf = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""),'base64')
    const data = {
      Bucket: process.env.SOURCE_BUCKETS,
      Key: 'prova.jpg',
      Body: buf,
      ContentEncoding: 'base64',
      ContentType: 'image/jpeg'
    };
    await s3.putObject(data).promise();
  }
}


module.exports=ImageUpload;
