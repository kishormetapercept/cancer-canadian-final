const imageHrefService = require('../services/imageHrefService');
const ResponseUtil = require('../utils/responseUtil');
const Logger = require('../utils/logger');

class ImageHrefController {
  async replaceHrefs(req, res) {
    try {
      const dryRun = Boolean(req.body && req.body.dryRun);
      Logger.info(`Starting image href replacement${dryRun ? ' (dry run)' : ''}.`);
      const result = await imageHrefService.replaceHrefs({ dryRun });
      Logger.success('Image href replacement completed.');
      return ResponseUtil.success(
        res,
        dryRun ? 'Image href dry run completed' : 'Image hrefs updated',
        result
      );
    } catch (error) {
      Logger.error(`Image href replacement failed: ${error.message}`);
      return ResponseUtil.serverError(res, 'Image href replacement failed', error.message);
    }
  }
}

module.exports = new ImageHrefController();
