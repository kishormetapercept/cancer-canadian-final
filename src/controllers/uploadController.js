const zipService = require('../services/zipService');
const xsltService = require('../services/xsltService');
const Validator = require('../utils/validator');
const ResponseUtil = require('../utils/responseUtil');
const Logger = require('../utils/logger');

class UploadController {
  async uploadZip(req, res) {
    Logger.upload(`Received zip upload request from ${req.ip}`);
    
    try {
      const validation = Validator.validateUploadRequest(req);
      if (!validation.isValid) {
        Logger.error(validation.error);
        return ResponseUtil.badRequest(res, validation.error);
      }

      Logger.info(`File details: ${req.file.originalname} (${req.file.size} bytes)`);

      const result = await zipService.extractZip(req.file.path);

      Logger.info('Starting XSLT pipeline.');
      const xsltResult = await xsltService.processOutput(result.outputDir);
      Logger.success('XSLT processing completed.');

      return ResponseUtil.success(res, 'Zip file processed successfully', {
        extractedFiles: result.extractedCount,
        outputDirectory: result.outputDir,
        xsltProcessedFiles: xsltResult.processedFiles,
        xsltOutputDirectory: xsltResult.outputDir,
        originalFileName: req.file.originalname
      });

    } catch (error) {
      Logger.error(`Upload error: ${error.message}`);
      return ResponseUtil.serverError(res, 'Failed to process zip file', error.message);
    }
  }
}

module.exports = new UploadController();
