const multer = require('multer');
const path = require('path');
const { UPLOAD_DIR, MAX_FILE_SIZE } = require('../config/constants');
const Validator = require('../utils/validator');
const FileUtil = require('../utils/fileUtil');

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    FileUtil.ensureDirectory(UPLOAD_DIR);
    FileUtil.clearDirectory(UPLOAD_DIR);
    cb(null, UPLOAD_DIR);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: MAX_FILE_SIZE },
  fileFilter: (req, file, cb) => {
    if (Validator.isValidZipFile(file)) {
      cb(null, true);
    } else {
      cb(new Error('Only .zip files are allowed'), false);
    }
  }
});

module.exports = upload;