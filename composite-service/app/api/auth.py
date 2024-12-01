# JWT Auth

import os
import jwt
import time

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

auth = APIRouter()
security = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_jwt_token(user_data: dict) -> Dict[str, str]:
    """Create JWT token for authenticated user"""
    access_payload = {
        "tokenId": user_data["tokenId"],
        "exp": time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "iat": time.time(),
        "type": "access",
    }

    # Refresh token payload
    refresh_payload = {
        "tokenId": user_data["tokenId"],
        "exp": time.time() + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
        "iat": time.time(),
        "type": "refresh",
    }

    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(
        refresh_payload, JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def verify_jwt_token(token: str, is_refresh: bool = False) -> dict:
    """Verify JWT token and return payload"""
    try:
        secret = JWT_REFRESH_SECRET if is_refresh else JWT_SECRET_KEY
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])

        # Verify token type
        expected_type = "refresh" if is_refresh else "access"
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type")

        if payload["exp"] < time.time():
            raise HTTPException(status_code=401, detail="Token has expired")

        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token: HTTPBearer = Depends(security)):
    """Dependency to get current user from JWT token"""
    try:
        payload = verify_jwt_token(token.credentials)
        return payload
    except HTTPException as e:
        if e.detail == "Token has expired":
            # Let the frontend know specifically that the token expired
            e.detail = {"code": "token_expired", "message": "Token has expired"}
        raise e


@auth.post("/refresh")
async def refresh_tokens(request: Request):
    """Endpoint to refresh access token using refresh token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="No refresh token provided")

        refresh_token = auth_header.split(" ")[1]
        payload = verify_jwt_token(refresh_token, is_refresh=True)

        # Create new tokens
        user_data = {
            "tokenId": payload["tokenId"],
        }
        return create_jwt_token(user_data)

    except HTTPException as e:
        if e.detail == "Token has expired":
            # Both tokens expired, user needs to login again
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "refresh_token_expired",
                    "message": "Refresh token expired, please login again",
                },
            )
        raise e


@auth.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is protected", "user": current_user}


# Google OAuth callback route
@auth.post("/login")
async def google_auth(token_info: dict):
    user_data = {
        "tokenId": token_info["tokenId"],
    }

    # Create JWT token
    token = create_jwt_token(user_data)
    return token
