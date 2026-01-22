const { ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES } = require('../config/constants');

class Validator {
  static isValidZipFile(file) {
    if (!file) return false;
    
    const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => 
      file.originalname.toLowerCase().endsWith(ext)
    );
    
    const hasValidMimeType = ALLOWED_MIME_TYPES.includes(file.mimetype);
    
    return hasValidExtension || hasValidMimeType;
  }

  static validateUploadRequest(req) {
    if (!req.file) {
      return { isValid: false, error: 'No zip file provided' };
    }

    if (!this.isValidZipFile(req.file)) {
      return { isValid: false, error: 'Only .zip files are allowed' };
    }

    return { isValid: true };
  }
}

module.exports = Validator;