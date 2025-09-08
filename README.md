# OCR Analysis Service

A full-stack OCR (Optical Character Recognition) service using FastAPI backend with LangGraph and a simple Express.js frontend for file uploads.

## Architecture

- **Backend**: FastAPI + LangGraph + OpenAI GPT-4o-mini for OCR processing
- **Frontend**: Express.js server with file upload interface
- **Logging**: Rich console logging with token usage and cost tracking

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd back/
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```bash
echo "LLM_API_KEY=your_openai_api_key_here" > .env
```

5. Run the backend server:
```bash
# Standard mode (INFO level logging - shows tokens/cost)
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Debug mode (shows extracted text as well)
LOG_LEVEL=DEBUG uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd front/
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Run the frontend server:
```bash
npm run dev
# or
npm start
```

The frontend will be available at `http://localhost:3000`

## Docker Setup (Recommended)

### Prerequisites
- Docker and Docker Compose v2 installed

### Building Docker Images

From the project root directory:

```bash
# Build backend image
docker build -t antonbiz/agent-back:1.0 ./back

# Build frontend image  
docker build -t antonbiz/agent-front:1.0 ./front
```

### Running with Docker Compose

```bash
# Start all services
docker compose up

# Start in detached mode
docker compose up -d

# View logs from all containers
docker compose logs -f

# Stop all services
docker compose down

# Rebuild and start (after code changes)
docker compose up --build

# Or in short:
docker compose down && docker build -f back/Dockerfile.back -t antonbiz/agent-back:1.0 ./back && docker build -f front/Dockerfile.front -t antonbiz/agent-front:1.0 ./front && docker compose up
```

The application will be available at:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Usage

1. Make sure both backend and frontend servers are running
2. Open your browser and go to `http://localhost:3000`
3. Drag and drop an image file or use the file picker
4. The extracted text will be displayed along with usage statistics

## Supported Image Formats

- JPEG/JPG
- PNG
- WebP
- GIF
- BMP
- TIFF

## API Endpoints

- `GET /` - Health check
- `POST /analyze` - Upload and analyze an image file

## Dependencies

### Backend (Python)
- FastAPI - Web framework
- LangGraph - Graph-based workflow orchestration
- LangChain OpenAI - OpenAI API integration
- Rich - Beautiful console logging
- Uvicorn - ASGI server

### Frontend (Node.js)
- Express.js - Web server framework
- Multer - File upload handling
- Axios - HTTP client
- form-data - Multipart form data handling
