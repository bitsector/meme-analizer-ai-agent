const express = require('express');
const multer = require('multer');
const axios = require('axios');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

const upload = multer({ dest: 'uploads/' });

app.use(express.static('public'));
app.use(express.json());

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index-auth.html'));
});

// Proxy authentication endpoints to backend
app.get('/api/auth/login', async (req, res) => {
    try {
        const response = await axios.get(`${BACKEND_URL}/auth/login`, {
            params: req.query
        });
        res.json(response.data);
    } catch (error) {
        console.error('Auth login proxy error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({ 
            error: error.response?.data?.detail || error.message 
        });
    }
});

app.post('/api/auth/callback', async (req, res) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/auth/callback`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error('Auth callback proxy error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({ 
            error: error.response?.data?.detail || error.message 
        });
    }
});

app.get('/api/auth/me', async (req, res) => {
    try {
        const response = await axios.get(`${BACKEND_URL}/auth/me`, {
            headers: {
                'Authorization': req.headers.authorization
            }
        });
        res.json(response.data);
    } catch (error) {
        console.error('Auth me proxy error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({ 
            error: error.response?.data?.detail || error.message 
        });
    }
});

app.post('/api/auth/logout', async (req, res) => {
    try {
        const response = await axios.post(`${BACKEND_URL}/auth/logout`);
        res.json(response.data);
    } catch (error) {
        console.error('Auth logout proxy error:', error.response?.data || error.message);
        res.status(error.response?.status || 500).json({ 
            error: error.response?.data?.detail || error.message 
        });
    }
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
                'Authorization': req.headers.authorization
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