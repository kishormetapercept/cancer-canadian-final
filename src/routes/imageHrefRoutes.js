const express = require('express');
const imageHrefController = require('../controllers/imageHrefController');

const router = express.Router();

router.post('/replace-hrefs', imageHrefController.replaceHrefs);

module.exports = router;
