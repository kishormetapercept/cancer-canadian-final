const express = require('express');
const upload = require('../middlewares/uploadMiddleware');
const uploadController = require('../controllers/uploadController');

const router = express.Router();

router.post('/zip', upload.single('zipfile'), uploadController.uploadZip);

module.exports = router;