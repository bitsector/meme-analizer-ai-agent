from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from services import analyze_image

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
            "content_type": result["content_type"],
            "search_results": result["search_results"],
            "meme_name": result["meme_name"],
            "explain_humor": result["explain_humor"],
            "social_media_platform": result["social_media_platform"],
            "poster_name": result["poster_name"],
            "sentiment": result["sentiment"],
            "is_political": result["is_political"],
            "is_outrage": result["is_outrage"],
            "usage": result["usage"]
        }
    
    except Exception as e:
        error_msg = str(e)
        if "unsupported_country_region_territory" in error_msg:
            raise HTTPException(
                status_code=403, 
                detail="OpenAI API is not available in your region. Please use a VPN or contact support for alternative solutions."
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def root():
    return {"message": "OCR Analysis API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)