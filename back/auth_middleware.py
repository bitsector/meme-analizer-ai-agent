"""
Authentication middleware for Google OAuth integration
Handles JWT token validation and user session management
"""

import os
import jwt
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from authlib.integrations.httpx_client import AsyncOAuth2Client
from logging_config import get_logger

logger = get_logger(__name__)

# Security scheme for FastAPI docs
security = HTTPBearer()


def get_secret(secret_name: str) -> str:
    """Read secret from Docker secrets or environment variable"""
    # Try Docker secrets first
    secret_file = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_file):
        logger.debug(f"Reading secret {secret_name} from Docker secrets")
        return Path(secret_file).read_text().strip()
    
    # Fallback to environment variable
    env_value = os.getenv(secret_name.upper())
    if env_value:
        logger.debug(f"Reading secret {secret_name} from environment")
        return env_value
    
    raise ValueError(f"Secret {secret_name} not found in Docker secrets or environment")


class AuthConfig:
    """OAuth configuration class"""
    
    def __init__(self):
        try:
            self.google_client_id = get_secret("google_oauth_client_id")
            self.google_client_secret = get_secret("google_oauth_client_secret")  
            self.jwt_secret = get_secret("jwt_secret")
            self.google_redirect_uri = "http://localhost:8000/auth/callback"
            self.google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            self.google_token_url = "https://oauth2.googleapis.com/token"
            self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            
            # Log successful configuration (without secrets)
            logger.info("OAuth configuration loaded successfully")
            logger.info(f"Client ID (first 20 chars): {self.google_client_id[:20]}...")
            logger.info(f"Client Secret (length): {len(self.google_client_secret)} chars")
            logger.info(f"JWT Secret (length): {len(self.jwt_secret)} chars")
            logger.info(f"Redirect URI: {self.google_redirect_uri}")
            
        except Exception as e:
            logger.error(f"Failed to load OAuth configuration: {str(e)}")
            raise


auth_config = AuthConfig()


class AuthService:
    """Google OAuth service for user authentication"""
    
    @staticmethod
    def get_google_auth_url() -> str:
        """Generate Google OAuth authorization URL"""
        try:
            logger.info(f"Creating OAuth client with client_id: {auth_config.google_client_id[:20]}...")
            logger.info(f"Redirect URI: {auth_config.google_redirect_uri}")
            
            oauth_client = AsyncOAuth2Client(
                client_id=auth_config.google_client_id,
                client_secret=auth_config.google_client_secret,
                redirect_uri=auth_config.google_redirect_uri
            )
            
            authorization_url, state = oauth_client.create_authorization_url(
                auth_config.google_auth_url,
                scope=["openid", "email", "profile"]
            )
            
            logger.info(f"Generated auth URL: {authorization_url}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to generate Google auth URL: {str(e)}")
            raise
    
    @staticmethod
    async def exchange_code_for_token(authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token and user info"""
        logger.info(f"Starting token exchange for authorization code: {authorization_code[:10]}...")
        
        oauth_client = AsyncOAuth2Client(
            client_id=auth_config.google_client_id,
            client_secret=auth_config.google_client_secret,
            redirect_uri=auth_config.google_redirect_uri
        )
        
        try:
            # Exchange authorization code for access token
            logger.info("Exchanging authorization code for access token...")
            async with httpx.AsyncClient() as client:
                token_data = {
                    'client_id': auth_config.google_client_id,
                    'client_secret': auth_config.google_client_secret,
                    'code': authorization_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': auth_config.google_redirect_uri,
                }
                
                token_response = await client.post(
                    auth_config.google_token_url,
                    data=token_data
                )
                
                if token_response.status_code != 200:
                    logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
                    raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
                
                token_response_data = token_response.json()
            
            logger.info("Successfully obtained access token from Google")
            logger.debug(f"Token response keys: {list(token_response_data.keys())}")
            
            # Get user info from Google
            logger.info("Fetching user info from Google...")
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token_response_data['access_token']}"}
                user_response = await client.get(auth_config.google_userinfo_url, headers=headers)
                
                if user_response.status_code != 200:
                    logger.error(f"Failed to get user info: {user_response.status_code} - {user_response.text}")
                    raise HTTPException(status_code=400, detail="Failed to get user info from Google")
                
                user_info = user_response.json()
                logger.info(f"Successfully got user info for: {user_info.get('email', 'unknown')}")
            
            return {
                "google_id": user_info["id"],
                "email": user_info["email"], 
                "name": user_info["name"],
                "avatar_url": user_info.get("picture"),
                "access_token": token_response_data["access_token"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to authenticate with Google: {str(e)}"
            )
    
    @staticmethod
    def create_jwt_token(user_info: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        import datetime
        
        payload = {
            "google_id": user_info["google_id"],
            "email": user_info["email"],
            "name": user_info["name"],
            "avatar_url": user_info["avatar_url"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            "iat": datetime.datetime.utcnow()
        }
        
        token = jwt.encode(payload, auth_config.jwt_secret, algorithm="HS256")
        return token
    
    @staticmethod
    def verify_jwt_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, auth_config.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract current user from JWT token in request headers"""
    authorization: str = request.headers.get("authorization")
    
    if not authorization:
        return None
        
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split("Bearer ")[1]
    
    try:
        user_info = AuthService.verify_jwt_token(token)
        return user_info
    except HTTPException:
        return None


def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication - raise exception if not authenticated"""
    user = get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user