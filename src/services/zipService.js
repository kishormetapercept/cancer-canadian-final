const fs = require('fs');
const path = require('path');
const yauzl = require('yauzl');
const { OUTPUT_DIR } = require('../config/constants');
const Logger = require('../utils/logger');
const FileUtil = require('../utils/fileUtil');

class ZipService {
  constructor() {
    this.outputDir = path.join(process.cwd(), OUTPUT_DIR);
  }

  async extractZip(zipPath) {
    Logger.extract(`Starting zip extraction: ${zipPath}`);
    FileUtil.ensureDirectory(this.outputDir);
    FileUtil.clearDirectory(this.outputDir);

    return new Promise((resolve, reject) => {
      yauzl.open(zipPath, { lazyEntries: true }, (err, zipfile) => {
        if (err) {
          Logger.error(`Error opening zip file: ${err.message}`);
          return reject(err);
        }

        Logger.info(`Zip file opened successfully, entries: ${zipfile.entryCount}`);
        const maxConcurrency = this._getConcurrency();
        const queue = [];
        const seen = new Set();
        let inFlight = 0;
        let extractedCount = 0;
        let ended = false;
        let rejected = false;

        const fail = (error) => {
          if (rejected) return;
          rejected = true;
          Logger.error(`Zip file error: ${error.message}`);
          try {
            zipfile.close();
          } catch (closeErr) {
            Logger.error(`Zip close error: ${closeErr.message}`);
          }
          reject(error);
        };

        const maybeFinish = () => {
          if (rejected) return;
          if (ended && inFlight === 0) {
            this._onExtractionComplete(extractedCount, resolve);
          }
        };

        const processQueue = () => {
          while (!rejected && queue.length > 0 && inFlight < maxConcurrency) {
            const entry = queue.shift();
            const started = this._processEntry(
              entry,
              zipfile,
              () => {
                extractedCount += 1;
                return extractedCount;
              },
              () => {
                inFlight -= 1;
                processQueue();
                maybeFinish();
              },
              fail
            );

            if (started) {
              inFlight += 1;
            }
          }
        };

        zipfile.on('entry', (entry) => {
          if (rejected) return;
          const validationError = this._validateEntry(entry, seen);
          if (validationError) {
            fail(new Error(validationError));
            return;
          }
          queue.push(entry);
          processQueue();
          if (!rejected) {
            zipfile.readEntry();
          }
        });
        zipfile.on('end', () => {
          ended = true;
          maybeFinish();
        });
        zipfile.on('error', fail);

        zipfile.readEntry();
      });
    });
  }

  _processEntry(entry, zipfile, onFileExtracted, onFileDone, reject) {
    const normalizedName = entry.normalizedName || this._normalizeEntryName(entry.fileName);
    if (!normalizedName) {
      reject(new Error(`Invalid zip entry path: ${entry.fileName}`));
      return false;
    }
    const outputPath = path.join(this.outputDir, normalizedName);

    if (/\/$/.test(entry.fileName)) {
      Logger.folder(`Creating directory: ${entry.fileName}`);
      FileUtil.ensureDirectory(outputPath);
      return false;
    } else {
      this._extractFile(entry, outputPath, zipfile, onFileExtracted, onFileDone, reject);
      return true;
    }
  }

  _extractFile(entry, outputPath, zipfile, onFileExtracted, onFileDone, reject) {
    Logger.file(`Extracting file: ${entry.fileName}`);

    zipfile.openReadStream(entry, (err, readStream) => {
      if (err) {
        Logger.error(`Error reading entry ${entry.fileName}: ${err.message}`);
        return reject(err);
      }

      let finished = false;
      const finish = () => {
        if (finished) return;
        finished = true;
        onFileDone();
      };

      const writeStream = FileUtil.createWriteStream(outputPath);
      readStream.pipe(writeStream);

      readStream.on('error', (streamErr) => {
        Logger.error(`Error reading stream ${entry.fileName}: ${streamErr.message}`);
        finish();
        reject(streamErr);
      });

      writeStream.on('close', () => {
        const currentCount = onFileExtracted();
        Logger.success(`Extracted: ${entry.fileName} (${currentCount}/${zipfile.entryCount})`);
        finish();
      });

      writeStream.on('error', (writeErr) => {
        Logger.error(`Error writing file ${entry.fileName}: ${writeErr.message}`);
        finish();
        reject(writeErr);
      });
    });
  }

  _onExtractionComplete(extractedCount, resolve) {
    Logger.complete(`Zip extraction completed! ${extractedCount} files extracted to: ${this.outputDir}`);
    resolve({ extractedCount, outputDir: this.outputDir });
  }

  _getConcurrency() {
    const raw = process.env.ZIP_EXTRACT_CONCURRENCY;
    const parsed = parseInt(raw, 10);
    if (!Number.isFinite(parsed) || parsed < 1) {
      return 4;
    }
    return Math.min(parsed, 32);
  }

  _normalizeEntryName(entryName) {
    const normalized = path.normalize(entryName);
    if (path.isAbsolute(normalized)) {
      return null;
    }
    if (normalized === '..' || normalized.startsWith(`..${path.sep}`)) {
      return null;
    }
    return normalized;
  }

  _validateEntry(entry, seen) {
    const normalizedName = this._normalizeEntryName(entry.fileName);
    if (!normalizedName) {
      return `Invalid zip entry path: ${entry.fileName}`;
    }

    const key = process.platform === 'win32' ? normalizedName.toLowerCase() : normalizedName;
    if (seen.has(key)) {
      return `Duplicate zip entry path: ${entry.fileName}`;
    }
    seen.add(key);
    entry.normalizedName = normalizedName;

    const outputPath = path.join(this.outputDir, normalizedName);
    if (fs.existsSync(outputPath)) {
      const stat = fs.statSync(outputPath);
      if (/\/$/.test(entry.fileName)) {
        if (!stat.isDirectory()) {
          return `Refusing to overwrite existing path: ${outputPath}`;
        }
      } else {
        return `Refusing to overwrite existing path: ${outputPath}`;
      }
    }

    return null;
  }
}

module.exports = new ZipService();
