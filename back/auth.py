import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import JWTError, jwt as jose_jwt

security = HTTPBearer()

class AuthManager:
    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID", "common")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-super-secret-key-change-this")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
        if not self.client_id:
            raise ValueError("AZURE_CLIENT_ID environment variable is required")
        if not self.client_secret:
            raise ValueError("AZURE_CLIENT_SECRET environment variable is required")

    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT access token for the user"""
        expire = datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        to_encode = {
            "sub": user_data.get("id"),
            "email": user_data.get("mail") or user_data.get("userPrincipalName"),
            "name": user_data.get("displayName"),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jose_jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jose_jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token from Microsoft"""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email User.Read"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
        return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user information")
            
        return response.json()

    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        """Generate Microsoft OAuth2 authorization URL"""
        base_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email User.Read",
            "response_mode": "query"
        }
        
        if state:
            params["state"] = state
            
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"

auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional dependency to get current user if authenticated"""
    if not credentials:
        return None
        
    token = credentials.credentials
    return auth_manager.verify_token(token)