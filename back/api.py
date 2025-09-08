from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import uvicorn
from services import analyze_image
from auth import auth_manager, get_current_user, get_optional_user
from typing import Optional
import uuid

app = FastAPI(title="OCR Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth endpoints
@app.get("/auth/login")
async def login(redirect_uri: str = Query(...)):
    """Initiate Microsoft OAuth login"""
    state = str(uuid.uuid4())
    auth_url = auth_manager.get_auth_url(redirect_uri, state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }

@app.post("/auth/callback")
async def auth_callback(code: str, redirect_uri: str, state: Optional[str] = None):
    """Handle OAuth callback and exchange code for JWT"""
    try:
        # Exchange authorization code for access token
        token_response = await auth_manager.exchange_code_for_token(code, redirect_uri)
        access_token = token_response["access_token"]
        
        # Get user information from Microsoft Graph
        user_info = await auth_manager.get_user_info(access_token)
        
        # Create our own JWT token
        jwt_token = auth_manager.create_access_token(user_info)
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user_info.get("id"),
                "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                "name": user_info.get("displayName"),
                "given_name": user_info.get("givenName"),
                "surname": user_info.get("surname")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user": {
            "id": current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("name")
        }
    }

@app.post("/auth/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Logged out successfully"}

@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
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
            "usage": result["usage"],
            "analyzed_by": current_user.get("email")
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