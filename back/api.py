from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from services import analyze_image
import io

app = FastAPI(title="OCR Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    try:
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 
            'image/gif', 'image/bmp', 'image/tiff'
        ]
        
        if not (file.content_type and (file.content_type in allowed_types or file.content_type.startswith('image/'))):
            raise HTTPException(status_code=400, detail=f"File must be an image. Received: {file.content_type}")
        
        contents = await file.read()
        
        result = analyze_image(contents)
        
        return {
            "filename": file.filename,
            "text": result["text"],
            "usage": result["usage"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "OCR Analysis API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)