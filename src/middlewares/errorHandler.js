const multer = require('multer');
const Logger = require('../utils/logger');
const ResponseUtil = require('../utils/responseUtil');

const errorHandler = (err, req, res, next) => {
  Logger.error(`Error: ${err.message}`);

  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return ResponseUtil.badRequest(res, 'File size too large');
    }
    return ResponseUtil.badRequest(res, err.message);
  }

  if (err.message === 'Only .zip files are allowed') {
    return ResponseUtil.badRequest(res, err.message);
  }

  return ResponseUtil.serverError(res, 'Internal server error', err.message);
};

module.exports = errorHandler;