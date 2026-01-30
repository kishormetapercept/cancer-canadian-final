const fs = require('fs');
const path = require('path');
const Logger = require('./logger');

class FileUtil {
  static ensureDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  static deleteFile(filePath) {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  }

  static clearDirectory(dirPath) {const { exec } = require('child_process');
  const path = require('path');
  const { OUTPUT_DIR } = require('../config/constants');
  const Logger = require('../utils/logger');

  class ZipService {
    constructor() {
      this.outputDir = path.join(process.cwd(), OUTPUT_DIR);
    }

    async extractZip(zipPath) {
      Logger.extract(`Starting Python zip extraction: ${zipPath}`);
      
      return new Promise((resolve, reject) => {
        const pythonScript = path.join(__dirname, '../../scripts/unzip.py');
        const cmd = `python "${pythonScript}" "${zipPath}" "${this.outputDir}"`;
        
        exec(cmd, (error, stdout, stderr) => {
          if (error) {
            Logger.error(`Python extraction failed: ${error.message}`);
            return reject(error);
          }
          
          const extractedMatch = stdout.match(/EXTRACTED:(\d+)/);
          const errorMatch = stdout.match(/ERROR:(.+)/);
          
          if (errorMatch) {
            Logger.error(`Python error: ${errorMatch[1]}`);
            return reject(new Error(errorMatch[1]));
          }
          
          const extractedCount = extractedMatch ? parseInt(extractedMatch[1]) : 0;
          
          Logger.complete(`Python extraction completed! ${extractedCount} files extracted to: ${this.outputDir}`);
          resolve({ extractedCount, outputDir: this.outputDir });
        });
      });
    }
  }

  module.exports = new ZipService();

    if (fs.existsSync(dirPath)) {
      fs.rmSync(dirPath, { recursive: true, force: true });
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  static createWriteStream(filePath) {
    this.ensureDirectory(path.dirname(filePath));
    return fs.createWriteStream(filePath);
  }
}

module.exports = FileUtil;
