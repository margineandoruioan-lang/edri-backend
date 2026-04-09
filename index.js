const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));

app.use(express.json());

app.get('/api/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok', 
    project: 'EDRI',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/decisions', async (req, res) => {
  try {
    res.json({ decisions: [], message: 'EDRI Backend live' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`EDRI backend running on port ${PORT}`);
});
