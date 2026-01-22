class Logger {
  static info(message) {
    console.log(`ℹ️ ${message}`);
  }

  static success(message) {
    console.log(`✅ ${message}`);
  }

  static error(message) {
    console.error(`❌ ${message}`);
  }

  static upload(message) {
    console.log(`📥 ${message}`);
  }

  static extract(message) {
    console.log(`🚀 ${message}`);
  }

  static file(message) {
    console.log(`📄 ${message}`);
  }

  static folder(message) {
    console.log(`📂 ${message}`);
  }

  static cleanup(message) {
    console.log(`🗑️ ${message}`);
  }

  static complete(message) {
    console.log(`🎉 ${message}`);
  }
}

module.exports = Logger;