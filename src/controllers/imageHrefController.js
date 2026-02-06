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
      Logger.info(`Starting .dita relocation${dryRun ? ' (dry run)' : ''}.`);
      const ditaResult = await imageHrefService.relocateDitaFiles({ dryRun });
      Logger.success('.dita relocation completed.');
      Logger.info(`Starting blob copy${dryRun ? ' (dry run)' : ''}.`);
      const blobCopyResult = await imageHrefService.copyBlobToXslt({ dryRun });
      Logger.success('Blob copy completed.');
      Logger.info(`Starting blob href replacement${dryRun ? ' (dry run)' : ''}.`);
      const blobResult = await imageHrefService.replaceBlobImageHrefs({ dryRun });
      Logger.success('Blob href replacement completed.');
      Logger.info(`Starting xref href replacement${dryRun ? ' (dry run)' : ''}.`);
      const xrefResult = await imageHrefService.replaceXrefHrefs({ dryRun });
      Logger.success('Xref href replacement completed.');
      return ResponseUtil.success(
        res,
        dryRun ? 'Href replacement dry run completed' : 'Href replacements updated',
        {
          images: imageResult,
          blobCopy: blobCopyResult,
          blobImages: blobResult,
          xrefs: xrefResult,
          ditaRelocation: ditaResult
        }
      );
    } catch (error) {
      Logger.error(`Href replacement failed: ${error.message}`);
      return ResponseUtil.serverError(res, 'Href replacement failed', error.message);
    }
  }
}

module.exports = new ImageHrefController();
