class ResponseUtil {
  static success(res, message, data = null) {
    return res.json({
      success: true,
      message,
      ...(data && { data })
    });
  }

  static error(res, statusCode, message, error = null) {
    return res.status(statusCode).json({
      success: false,
      message,
      ...(error && { error })
    });
  }

  static badRequest(res, message) {
    return this.error(res, 400, message);
  }

  static serverError(res, message, error = null) {
    return this.error(res, 500, message, error);
  }
}

module.exports = ResponseUtil;