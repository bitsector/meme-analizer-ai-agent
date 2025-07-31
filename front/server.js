const express = require('express');
const multer = require('multer');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;
const BACKEND_URL = 'http://localhost:8000';

const upload = multer({ dest: 'uploads/' });

app.use(express.static('public'));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/upload', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        console.log(`File ${req.file.originalname} received`);
        
        const FormData = require('form-data');
        const formData = new FormData();
        const fileStream = fs.createReadStream(req.file.path);
        formData.append('file', fileStream, req.file.originalname);

        const response = await axios.post(`${BACKEND_URL}/analyze`, formData, {
            headers: {
                ...formData.getHeaders(),
            },
        });

        fs.unlinkSync(req.file.path);
        
        console.log(`File ${req.file.originalname} sent to backend successfully`);
        res.json(response.data);
    } catch (error) {
        console.error('Error processing file:', error.response?.data || error.message);
        res.status(500).json({ error: 'Failed to process file' });
    }
});

app.listen(PORT, () => {
    console.log(`Frontend server running on http://localhost:${PORT}`);
});