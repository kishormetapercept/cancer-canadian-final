# Zip Upload & Extract Feature

## Overview
This feature allows users to upload zip files which are automatically extracted to an `output` folder following the original folder structure.

## Features
- ✅ Modular architecture with separate service, controller, and routes
- ✅ Automatic output directory creation
- ✅ Preserves original folder structure during extraction
- ✅ Comprehensive logging from start to finish
- ✅ File validation (only .zip files allowed)
- ✅ Automatic cleanup of uploaded zip files
- ✅ 100MB file size limit
- ✅ Error handling and proper HTTP responses

## API Endpoint

### POST /api/upload/zip
Upload and extract a zip file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Field name: `zipfile`
- File type: .zip only
- Max size: 100MB

**Response:**
```json
{
  "success": true,
  "message": "Zip file uploaded and extracted successfully",
  "data": {
    "extractedFiles": 15,
    "outputDirectory": "C:\\Projects\\cancer-canadian\\output",
    "originalFileName": "my-files.zip"
  }
}
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the server:
```bash
npm run dev
```

3. Test the upload feature:
   - Visit: http://localhost:3000/test
   - Or use the API directly with tools like Postman

## File Structure
```
src/
├── controllers/
│   └── uploadController.js    # Handles upload requests
├── services/
│   └── zipService.js         # Zip extraction logic
├── routes/
│   └── uploadRoutes.js       # Upload route definitions
└── app.js                    # Main app with routes

uploads/                      # Temporary upload storage
output/                       # Extracted files destination
```

## Logging
The feature provides detailed logging throughout the process:
- 📥 Upload request received
- 📋 File details validation
- 📁 Directory creation
- 📦 Zip file processing
- 📂 Directory extraction
- 📄 File extraction progress
- ✅ Individual file completion
- 🎉 Overall completion
- 🗑️ Cleanup operations
- ❌ Error handling

## Error Handling
- Invalid file types (non-zip)
- Missing files in request
- File size limits exceeded
- Zip extraction errors
- File system errors
- Proper HTTP status codes and error messages