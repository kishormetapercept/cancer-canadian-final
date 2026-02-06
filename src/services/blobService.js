const fs = require('fs');
const path = require('path');
const Logger = require('../utils/logger');

class BlobService {
  async finalizeBlobExport() {
    const blobDir = path.join(
      process.cwd(),
      'Mike_Rice_Images-Export-CCS',
      'package',
      'blob'
    );
    const masterDir = path.join(blobDir, 'master');
    const outputDir = path.join(process.cwd(), 'output');
    const destDir = path.join(outputDir, 'blob');

    if (!fs.existsSync(blobDir)) {
      throw new Error(`Blob directory not found: ${blobDir}`);
    }
    if (!fs.existsSync(masterDir)) {
      throw new Error(`Blob master directory not found: ${masterDir}`);
    }

    const entries = await fs.promises.readdir(masterDir, { withFileTypes: true });
    let renamed = 0;

    for (const entry of entries) {
      if (!entry.isFile()) continue;
      const oldPath = path.join(masterDir, entry.name);
      const newName = `${path.parse(entry.name).name}.jpeg`;
      if (entry.name === newName) continue;
      const newPath = path.join(masterDir, newName);

      if (fs.existsSync(newPath)) {
        await fs.promises.unlink(newPath);
      }

      await fs.promises.rename(oldPath, newPath);
      renamed += 1;
    }

    await fs.promises.mkdir(outputDir, { recursive: true });
    if (fs.existsSync(destDir)) {
      await fs.promises.rm(destDir, { recursive: true, force: true });
    }

    await this.copyDir(blobDir, destDir);

    Logger.complete(
      `[BLOB] Renamed ${renamed} file(s) to .jpeg and copied blob to output.`
    );

    return {
      renamedFiles: renamed,
      sourceDir: blobDir,
      destDir
    };
  }

  async copyDir(srcDir, destDir) {
    await fs.promises.mkdir(destDir, { recursive: true });
    const entries = await fs.promises.readdir(srcDir, { withFileTypes: true });

    for (const entry of entries) {
      const srcPath = path.join(srcDir, entry.name);
      const destPath = path.join(destDir, entry.name);

      if (entry.isDirectory()) {
        await this.copyDir(srcPath, destPath);
        continue;
      }

      if (entry.isFile()) {
        await fs.promises.copyFile(srcPath, destPath);
      }
    }
  }
}

module.exports = new BlobService();
