const express = require("express");
const cors = require("cors");
const path = require('path');
const uploadRoutes = require('./routes/uploadRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

app.use(cors());
app.use(express.json());

app.get('/test', (req, res) => {
  res.sendFile(path.join(__dirname, '../test-upload.html'));
});

app.use('/api/upload', uploadRoutes);

app.use(errorHandler);

app.use((req, res) => {
  res.status(404).json({ message: "Route not found" });
});

module.exports = app;