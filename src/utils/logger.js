class Logger {
  static _write(message, isError = false) {
    if (isError) {
      console.error(message);
    } else {
      console.log(message);
    }
  }

  static info(message) {
    Logger._write(`ℹ️ ${message}`);
  }

  static success(message) {
    Logger._write(`✅ ${message}`);
  }

  static error(message) {
    Logger._write(`❌ ${message}`, true);
  }

  static upload(message) {
    Logger._write(`📥 ${message}`);
  }

  static extract(message) {
    Logger._write(`🚀 ${message}`);
  }

  static file(message) {
    Logger._write(`📄 ${message}`);
  }

  static folder(message) {
    Logger._write(`📂 ${message}`);
  }

  static cleanup(message) {
    Logger._write(`🗑️ ${message}`);
  }

  static complete(message) {
    Logger._write(`🎉 ${message}`);
  }
}

module.exports = Logger;
