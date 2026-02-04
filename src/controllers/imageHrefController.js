const imageHrefService = require('../services/imageHrefService');
const ResponseUtil = require('../utils/responseUtil');
const Logger = require('../utils/logger');

class ImageHrefController {
  async replaceHrefs(req, res) {
    try {
      const dryRun = Boolean(req.body && req.body.dryRun);
      Logger.info(`Starting image href replacement${dryRun ? ' (dry run)' : ''}.`);
      const imageResult = await imageHrefService.replaceHrefs({ dryRun });
      Logger.success('Image href replacement completed.');
      Logger.info(`Starting xref href replacement${dryRun ? ' (dry run)' : ''}.`);
      const xrefResult = await imageHrefService.replaceXrefHrefs({ dryRun });
      Logger.success('Xref href replacement completed.');
      Logger.info(`Starting .dita relocation${dryRun ? ' (dry run)' : ''}.`);
      const ditaResult = await imageHrefService.relocateDitaFiles({ dryRun });
      Logger.success('.dita relocation completed.');
      return ResponseUtil.success(
        res,
        dryRun ? 'Href replacement dry run completed' : 'Href replacements updated',
        { images: imageResult, xrefs: xrefResult, ditaRelocation: ditaResult }
      );
    } catch (error) {
      Logger.error(`Href replacement failed: ${error.message}`);
      return ResponseUtil.serverError(res, 'Href replacement failed', error.message);
    }
  }
}

module.exports = new ImageHrefController();
