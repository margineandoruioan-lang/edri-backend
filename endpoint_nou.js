/**
 * EDRI — Endpoint NOU pentru procesare documente
 * DE ADAUGAT la sfarsitul fisierului server.js existent
 * NU se modifica nimic altceva
 */

const { execFile } = require('child_process');
const path = require('path');
const fs = require('fs');
const multer = require('multer');

// Upload temporar
const upload = multer({ 
  dest: '/tmp/edri_uploads/',
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB max
});

// POST /api/process-document
// Primeste un fisier si returneaza indicatorii financiari
app.post('/api/process-document', upload.single('document'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Niciun fisier primit' });
  }

  const filePath = req.file.path;
  const filename = req.file.originalname;

  // Apeleaza document_processor.py
  execFile('python3', [
    path.join(__dirname, 'document_processor.py'),
    filePath,
    filename
  ], { timeout: 30000 }, (error, stdout, stderr) => {
    // Sterge fisierul temporar
    try { fs.unlinkSync(filePath); } catch(e) {}

    if (error) {
      return res.status(500).json({ 
        error: 'Eroare procesare document',
        details: stderr
      });
    }

    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch(e) {
      res.status(500).json({ error: 'Eroare parsare rezultat' });
    }
  });
});

// GET /api/email-status
// Verifica statusul monitorizarii emailului
app.get('/api/email-status', (req, res) => {
  res.json({
    monitoring: true,
    address: 'invoice@ddl-intelligentsolutions.com',
    interval_minutes: 5,
    formats_supported: ['xlsx','xls','pdf','docx','doc','html','csv','jpg','png'],
    method: 'Metoda 3 — Parsare nativa + AI fallback'
  });
});
