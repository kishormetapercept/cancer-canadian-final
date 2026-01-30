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
    FileUtil.ensureDirectory(this.outputDir);
    FileUtil.clearDirectory(this.outputDir);

    return new Promise((resolve, reject) => {
      yauzl.open(zipPath, { lazyEntries: true }, (err, zipfile) => {
        if (err) {
          Logger.error(`Error opening zip file: ${err.message}`);
          return reject(err);
        }

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
      FileUtil.ensureDirectory(outputPath);
      return false;
    } else {
      this._extractFile(entry, outputPath, zipfile, onFileExtracted, onFileDone, reject);
      return true;
    }
  }

  _extractFile(entry, outputPath, zipfile, onFileExtracted, onFileDone, reject) {
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
        onFileExtracted();
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
    const removedDirs = this._cleanupLanguageVersions();
    const promoted = this._promoteLanguageXmlFiles();
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
    const parts = entryName.split(/[\\/]+/);
    if (parts.length === 0) {
      return null;
    }

    const isDir = /[\\/]$/.test(entryName);
    if (parts[parts.length - 1] === '') {
      parts.pop();
    }
    if (parts.length === 0) {
      return null;
    }

    const lastIndex = parts.length - 1;
    const mapped = parts.map((part, idx) => {
      if (part === '.' || part === '..') {
        return null;
      }
      if (idx === lastIndex && !isDir) {
        return part;
      }
      return this._transformDirectoryName(part);
    });

    if (mapped.some((part) => part === null)) {
      return null;
    }

    const normalized = path.normalize(path.join(...mapped));
    if (path.isAbsolute(normalized)) {
      return null;
    }
    if (normalized === '..' || normalized.startsWith(`..${path.sep}`)) {
      return null;
    }
    return normalized;
  }

  _transformDirectoryName(name) {
    let transformed = name;
    if (/^\{[^}]+\}$/.test(transformed)) {
      transformed = transformed.slice(1, -1);
    }
    transformed = transformed.toLowerCase();
    return transformed.replace(/ /g, '_');
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

  _cleanupLanguageVersions() {
    const targets = new Set(['en', 'fr']);
    let removedDirs = 0;

    const walk = (dirPath) => {
      let entries;
      try {
        entries = fs.readdirSync(dirPath, { withFileTypes: true });
      } catch (err) {
        return;
      }

      const baseName = path.basename(dirPath).toLowerCase();
      let keepNumericName = null;

      if (targets.has(baseName)) {
        const numericDirs = entries
          .filter((entry) => entry.isDirectory() && /^\d+$/.test(entry.name))
          .map((entry) => ({ name: entry.name, value: Number(entry.name) }));

        if (numericDirs.length > 1) {
          numericDirs.sort((a, b) => {
            if (a.value !== b.value) return a.value - b.value;
            return a.name.localeCompare(b.name);
          });
          keepNumericName = numericDirs[numericDirs.length - 1].name;

          for (const entry of numericDirs) {
            if (entry.name === keepNumericName) continue;
            const targetPath = path.join(dirPath, entry.name);
            try {
              fs.rmSync(targetPath, { recursive: true, force: true });
              removedDirs += 1;
            } catch (err) {
              Logger.error(`Failed to remove folder ${targetPath}: ${err.message}`);
            }
          }
        } else if (numericDirs.length === 1) {
          keepNumericName = numericDirs[0].name;
        }
      }

      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        if (targets.has(baseName) && /^\d+$/.test(entry.name) && keepNumericName && entry.name !== keepNumericName) {
          continue;
        }
        walk(path.join(dirPath, entry.name));
      }
    };

    walk(this.outputDir);
    return removedDirs;
  }

  _promoteLanguageXmlFiles() {
    const targets = new Set(['en', 'fr']);
    let moved = 0;

    const safeRemove = (targetPath) => {
      if (!fs.existsSync(targetPath)) {
        return;
      }
      const stat = fs.statSync(targetPath);
      if (stat.isDirectory()) {
        fs.rmSync(targetPath, { recursive: true, force: true });
      } else {
        fs.unlinkSync(targetPath);
      }
    };

    const removeIfEmpty = (dirPath) => {
      try {
        const remaining = fs.readdirSync(dirPath);
        if (remaining.length === 0) {
          fs.rmdirSync(dirPath);
        }
      } catch (err) {
        return;
      }
    };

    const walk = (dirPath) => {
      let entries;
      try {
        entries = fs.readdirSync(dirPath, { withFileTypes: true });
      } catch (err) {
        return;
      }

      const baseName = path.basename(dirPath);
      const parentName = path.basename(path.dirname(dirPath));
      const isVersionDir = /^\d+$/.test(baseName);
      const langName = parentName.toLowerCase();

      if (isVersionDir && targets.has(langName)) {
        const xmlEntry = entries.find((entry) => entry.name === 'xml');
        if (xmlEntry) {
          const xmlPath = path.join(dirPath, xmlEntry.name);
          const destDir = path.dirname(path.dirname(dirPath));
          const destPath = path.join(destDir, `${langName}_xml`);
          FileUtil.ensureDirectory(destDir);
          safeRemove(destPath);
          fs.renameSync(xmlPath, destPath);
          removeIfEmpty(dirPath);
          removeIfEmpty(path.dirname(dirPath));
          moved += 1;
        }
      }

      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        if (entry.name === 'xml') continue;
        walk(path.join(dirPath, entry.name));
      }
    };

    walk(this.outputDir);
    return moved;
  }
}

module.exports = new ZipService();
