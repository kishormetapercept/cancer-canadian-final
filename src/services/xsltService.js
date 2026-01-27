const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { XSLT_OUTPUT_DIR } = require('../config/constants');
const Logger = require('../utils/logger');

class XsltService {
  async processOutput(inputDir) {
    const scriptPath = path.join(process.cwd(), 'scripts', 'xslt_pipeline.py');
    const outputDir = path.join(process.cwd(), XSLT_OUTPUT_DIR);
    const pythonBin = process.env.PYTHON_BIN || 'python';
    const workers = parseInt(process.env.XSLT_WORKERS, 10);

    if (fs.existsSync(outputDir)) {
      fs.rmSync(outputDir, { recursive: true, force: true });
      Logger.cleanup(`Cleared directory: ${outputDir}`);
    }

    const args = [
      scriptPath,
      '--input',
      inputDir,
      '--output-dir',
      outputDir,
      '--pattern',
      '*_xml',
      '--overwrite',
      '--quiet',
      '--step-logs'
    ];

    if (Number.isFinite(workers) && workers > 0) {
      args.push('--workers', String(workers));
    }

    return new Promise((resolve, reject) => {
      const child = spawn(pythonBin, args, {
        cwd: process.cwd(),
        windowsHide: true
      });

      let doneCount = null;
      let failedCount = null;
      let errorLines = 0;
      let stderrLines = 0;
      const maxLogLines = 25;
      let lastStdoutWasError = false;

      const logErrorLine = (line) => {
        errorLines += 1;
        if (errorLines <= maxLogLines) {
          Logger.error(`[XSLT] ${line}`);
        } else if (errorLines === maxLogLines + 1) {
          Logger.error('[XSLT] Additional errors suppressed.');
        }
      };

      const logStderrLine = (line) => {
        if (!line) return;
        if (line.includes('Error in sys.excepthook') || line.includes('Original exception was:')) {
          return;
        }
        stderrLines += 1;
        if (stderrLines <= maxLogLines) {
          Logger.error(`[XSLT] ${line}`);
        } else if (stderrLines === maxLogLines + 1) {
          Logger.error('[XSLT] Additional stderr output suppressed.');
        }
      };

      const stdoutReader = readline.createInterface({ input: child.stdout });
      stdoutReader.on('line', (line) => {
        if (!line) return;
        if (line.startsWith('STEP:')) {
          lastStdoutWasError = false;
          Logger.info(`[XSLT] ${line}`);
          return;
        }
        if (line.startsWith('ERROR:')) {
          lastStdoutWasError = true;
          logErrorLine(line);
          return;
        }
        if (line.startsWith('FAILED:')) {
          lastStdoutWasError = false;
          failedCount = parseInt(line.split(':')[1], 10);
          return;
        }
        if (line.startsWith('DONE:')) {
          lastStdoutWasError = false;
          doneCount = parseInt(line.split(':')[1], 10);
          return;
        }
        if (line.startsWith('REPORT:')) {
          lastStdoutWasError = false;
          Logger.info(`[XSLT] ${line}`);
          return;
        }

        if (lastStdoutWasError) {
          logErrorLine(line);
          return;
        }

        Logger.info(`[XSLT] ${line}`);
      });

      const stderrReader = readline.createInterface({ input: child.stderr });
      stderrReader.on('line', (line) => {
        if (!line) return;
        logStderrLine(line);
      });

      child.on('error', (err) => {
        reject(err);
      });

      child.on('close', (code) => {
        stdoutReader.close();
        stderrReader.close();

        if (code !== 0) {
          return reject(
            new Error(`XSLT pipeline failed with exit code ${code}`)
          );
        }

        if (failedCount && failedCount > 0) {
          return reject(
            new Error(`XSLT pipeline reported ${failedCount} failed file(s)`)
          );
        }

        resolve({
          inputDir,
          outputDir,
          processedFiles: doneCount,
          failedFiles: failedCount || 0,
          errorLines
        });
      });
    });
  }
}

module.exports = new XsltService();
