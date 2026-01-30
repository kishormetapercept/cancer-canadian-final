const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');
const Logger = require('../utils/logger');

class ImageHrefService {
  replaceHrefs(options = {}) {
    const { dryRun = false } = options;
    const scriptPath = path.join(process.cwd(), 'scripts', 'update_image_hrefs.py');
    const imagesRoot = path.join(
      process.cwd(),
      'Mike_Rice_Images-Export-CCS',
      'package',
      'items',
      'master',
      'sitecore',
      'media library',
      'Images',
      'Cancer information'
    );
    const xsltRoot = path.join(process.cwd(), 'xslt_output');
    const pythonBin = process.env.PYTHON_BIN || 'python';

    const args = [
      scriptPath,
      '--images-root',
      imagesRoot,
      '--xslt-root',
      xsltRoot
    ];

    if (dryRun) {
      args.push('--dry-run');
    }

    return new Promise((resolve, reject) => {
      const child = spawn(pythonBin, args, {
        cwd: process.cwd(),
        windowsHide: true
      });

      let result = null;
      let stderrLines = 0;
      const maxStderrLines = 25;

      const stdoutReader = readline.createInterface({ input: child.stdout });
      stdoutReader.on('line', (line) => {
        if (!line) return;
        if (line.startsWith('RESULT:')) {
          try {
            result = JSON.parse(line.replace('RESULT:', ''));
          } catch (err) {
            Logger.error(`[IMG] Failed to parse result JSON: ${err.message}`);
          }
          return;
        }
        if (line.startsWith('ERROR:')) {
          Logger.error(`[IMG] ${line.replace('ERROR:', '')}`);
          return;
        }
        Logger.info(`[IMG] ${line}`);
      });

      const stderrReader = readline.createInterface({ input: child.stderr });
      stderrReader.on('line', (line) => {
        if (!line) return;
        stderrLines += 1;
        if (stderrLines <= maxStderrLines) {
          Logger.error(`[IMG] ${line}`);
        } else if (stderrLines === maxStderrLines + 1) {
          Logger.error('[IMG] Additional stderr output suppressed.');
        }
      });

      child.on('error', (err) => {
        reject(err);
      });

      child.on('close', (code) => {
        stdoutReader.close();
        stderrReader.close();

        if (code !== 0) {
          return reject(new Error(`Image href replacement failed with exit code ${code}`));
        }

        if (!result) {
          return reject(new Error('Image href replacement did not return a result'));
        }

        resolve(result);
      });
    });
  }
}

module.exports = new ImageHrefService();
