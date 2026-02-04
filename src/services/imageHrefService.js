const { spawn } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
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

  replaceXrefHrefs(options = {}) {
    const { dryRun = false } = options;
    const scriptPath = path.join(process.cwd(), 'scripts', 'update_xref_hrefs.py');
    const xsltRoot = path.join(process.cwd(), 'xslt_output');
    const pythonBin = process.env.PYTHON_BIN || 'python';

    const args = [
      scriptPath,
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
            Logger.error(`[XREF] Failed to parse result JSON: ${err.message}`);
          }
          return;
        }
        if (line.startsWith('ERROR:')) {
          Logger.error(`[XREF] ${line.replace('ERROR:', '')}`);
          return;
        }
        Logger.info(`[XREF] ${line}`);
      });

      const stderrReader = readline.createInterface({ input: child.stderr });
      stderrReader.on('line', (line) => {
        if (!line) return;
        stderrLines += 1;
        if (stderrLines <= maxStderrLines) {
          Logger.error(`[XREF] ${line}`);
        } else if (stderrLines === maxStderrLines + 1) {
          Logger.error('[XREF] Additional stderr output suppressed.');
        }
      });

      child.on('error', (err) => {
        reject(err);
      });

      child.on('close', (code) => {
        stdoutReader.close();
        stderrReader.close();

        if (code !== 0) {
          return reject(new Error(`Xref href replacement failed with exit code ${code}`));
        }

        if (!result) {
          return reject(new Error('Xref href replacement did not return a result'));
        }

        resolve(result);
      });
    });
  }

  async relocateDitaFiles(options = {}) {
    const { dryRun = false } = options;
    const xsltRoot = path.join(process.cwd(), 'xslt_output');
    let rootEntries = [];
    try {
      rootEntries = await fs.promises.readdir(xsltRoot, { withFileTypes: true });
    } catch (err) {
      rootEntries = [];
    }
    const roots = rootEntries
      .filter((entry) => entry.isDirectory() && entry.name !== '_tmp')
      .map((entry) => path.join(xsltRoot, entry.name));
    const guidPattern = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    const targetDirs = [];
    const reservedDestinations = new Set();

    const collectTargets = async (dirPath) => {
      let entries;
      try {
        entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
      } catch (err) {
        return;
      }

      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        const fullPath = path.join(dirPath, entry.name);
        if (entry.name === '_local' || guidPattern.test(entry.name)) {
          targetDirs.push(fullPath);
          continue;
        }
        await collectTargets(fullPath);
      }
    };

    for (const root of roots) {
      if (!fs.existsSync(root)) continue;
      await collectTargets(root);
    }

    const result = {
      roots,
      targetDirs: targetDirs.length,
      filesFound: 0,
      filesToMove: 0,
      filesMoved: 0,
      filesOverwritten: 0,
      filesRenamed: 0,
      dirsDeleted: 0,
      errors: []
    };

    const collectDitaFiles = async (dirPath, files) => {
      let entries;
      try {
        entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
      } catch (err) {
        return;
      }

      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        if (entry.isDirectory()) {
          await collectDitaFiles(fullPath, files);
          continue;
        }
        if (!entry.isFile()) continue;
        if (entry.name.toLowerCase().endsWith('.dita')) {
          files.push(fullPath);
        }
      }
    };

    const pathExists = async (targetPath) => {
      try {
        await fs.promises.stat(targetPath);
        return true;
      } catch (err) {
        return false;
      }
    };

    const buildSlug = (input) => {
      const sanitized = input
        .replace(/[\\/:*?"<>|]+/g, '_')
        .replace(/\s+/g, '_');
      if (sanitized.length <= 40) return sanitized;
      return sanitized.slice(sanitized.length - 40);
    };

    const buildHash = (value) => crypto.createHash('sha256').update(value).digest('hex').slice(0, 8);

    const getDestinationPath = async (sourcePath, parentDir, targetDir) => {
      const originalName = path.basename(sourcePath);
      let destPath = path.join(parentDir, originalName);
      const destKey = destPath.toLowerCase();
      const exists = await pathExists(destPath);
      if (!exists && !reservedDestinations.has(destKey)) {
        return { destPath, renamed: false };
      }

      const parsed = path.parse(originalName);
      const rel = path.relative(targetDir, sourcePath);
      let relDir = path.dirname(rel);
      if (!relDir || relDir === '.') {
        relDir = path.basename(targetDir);
      }
      const slug = buildSlug(relDir);
      const hash = buildHash(sourcePath);
      let candidate = `${parsed.name}__${slug}__${hash}${parsed.ext}`;
      destPath = path.join(parentDir, candidate);
      let i = 1;
      while ((await pathExists(destPath)) || reservedDestinations.has(destPath.toLowerCase())) {
        candidate = `${parsed.name}__${slug}__${hash}_${i}${parsed.ext}`;
        destPath = path.join(parentDir, candidate);
        i += 1;
      }

      return { destPath, renamed: true };
    };

    const moveFile = async (sourcePath, destPath) => {
      const resolvedSource = path.resolve(sourcePath);
      const resolvedDest = path.resolve(destPath);
      if (resolvedSource === resolvedDest) {
        return;
      }

      const destExists = await pathExists(destPath);
      if (destExists) {
        throw new Error(`Destination already exists: ${destPath}`);
      }

      if (dryRun) {
        return;
      }

      await fs.promises.mkdir(path.dirname(destPath), { recursive: true });
      try {
        await fs.promises.rename(sourcePath, destPath);
      } catch (err) {
        if (err.code !== 'EXDEV') {
          throw err;
        }
        await fs.promises.copyFile(sourcePath, destPath);
        await fs.promises.unlink(sourcePath);
      }
    };

    const removeDir = async (dirPath) => {
      if (dryRun) {
        return;
      }
      if (typeof fs.promises.rm === 'function') {
        await fs.promises.rm(dirPath, { recursive: true, force: true });
        return;
      }
      await fs.promises.rmdir(dirPath, { recursive: true });
    };

    for (const targetDir of targetDirs) {
      const parentDir = path.dirname(targetDir);
      const files = [];
      await collectDitaFiles(targetDir, files);
      result.filesFound += files.length;
      result.filesToMove += files.length;

      for (const sourcePath of files) {
        const { destPath, renamed } = await getDestinationPath(sourcePath, parentDir, targetDir);
        try {
          await moveFile(sourcePath, destPath);
          result.filesMoved += dryRun ? 0 : 1;
          if (renamed) {
            result.filesRenamed += 1;
          }
          reservedDestinations.add(destPath.toLowerCase());
        } catch (err) {
          result.errors.push({ sourcePath, destPath, error: err.message });
        }
      }

      try {
        await removeDir(targetDir);
        if (!dryRun) {
          result.dirsDeleted += 1;
        }
      } catch (err) {
        result.errors.push({ sourcePath: targetDir, destPath: targetDir, error: err.message });
      }
    }

    return result;
  }
}

module.exports = new ImageHrefService();
