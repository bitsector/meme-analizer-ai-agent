from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
from services import analyze_image
from auth_middleware import AuthService, get_current_user, require_auth
from typing import Optional

app = FastAPI(title="OCR Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup logging
@app.on_event("startup")
async def startup_event():
    print("🚀 BACKEND STARTING UP - OCR Analysis API")
    print("📋 Available endpoints:")
    print("   GET  /")
    print("   GET  /auth/login") 
    print("   GET  /auth/callback")
    print("   GET  /auth/me")
    print("   POST /auth/logout")
    print("   POST /analyze")
    print("✅ BACKEND READY!")

@app.on_event("shutdown") 
async def shutdown_event():
    print("🛑 BACKEND SHUTTING DOWN")

@app.post("/analyze")
async def analyze_file(request: Request, file: UploadFile = File(...)):
    # Optional authentication - get user if logged in but don't require it
    current_user = get_current_user(request)
    user_email = current_user["email"] if current_user else "anonymous"
    
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
            "analyzed_by": user_email  # Track who analyzed this image
        }
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"ANALYZE ERROR: {error_msg}")
        print(f"ANALYZE TRACEBACK: {traceback.format_exc()}")
        if "unsupported_country_region_territory" in error_msg:
            raise HTTPException(
                status_code=403, 
                detail="OpenAI API is not available in your region. Please use a VPN or contact support for alternative solutions."
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)

# =============================================================================
# AUTHENTICATION ENDPOINTS  
# =============================================================================

@app.get("/auth/login")
async def login():
    """Redirect to Google OAuth login"""
    try:
        print("LOGIN ENDPOINT CALLED")  # Console log
        google_auth_url = AuthService.get_google_auth_url()
        print(f"Generated auth URL: {google_auth_url}")  # Console log
        return {"auth_url": google_auth_url}
    except Exception as e:
        print(f"LOGIN ERROR: {str(e)}")  # Console log
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle Google OAuth callback"""
    try:
        print(f"CALLBACK ENDPOINT CALLED with code: {code[:10]}...")  # Console log
        
        # Exchange code for user info
        user_info = await AuthService.exchange_code_for_token(code)
        print(f"Got user info: {user_info.get('email', 'unknown')}")  # Console log
        
        # Create JWT token
        jwt_token = AuthService.create_jwt_token(user_info)
        print("Created JWT token successfully")  # Console log
        
        # In production, you might save user to database here
        # await save_user_to_db(user_info)
        
        # Redirect to frontend with token
        frontend_url = "http://localhost:3000"
        redirect_url = f"{frontend_url}/?token={jwt_token}"
        print(f"Redirecting to: {redirect_url[:50]}...")  # Console log
        return RedirectResponse(url=redirect_url)
        
    except HTTPException as he:
        print(f"CALLBACK HTTP ERROR: {he.detail}")  # Console log
        raise he
    except Exception as e:
        print(f"CALLBACK ERROR: {str(e)}")  # Console log
        import traceback
        print(f"CALLBACK TRACEBACK: {traceback.format_exc()}")  # Console log
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current authenticated user info"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "google_id": user["google_id"],
        "email": user["email"],
        "name": user["name"],
        "avatar_url": user["avatar_url"]
    }

@app.post("/auth/logout")
async def logout():
    """Logout user (stateless, just removes token on frontend)"""
    return {"message": "Logged out successfully"}

# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    print("ROOT ENDPOINT CALLED")  # Console log
    return {"message": "OCR Analysis API is running", "status": "healthy", "endpoints": ["/", "/auth/login", "/auth/callback", "/auth/me", "/analyze"]}

@app.get("/health")
async def health_check():
    print("HEALTH CHECK CALLED")  # Console log
    return {"status": "healthy", "timestamp": "2025-01-09"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)