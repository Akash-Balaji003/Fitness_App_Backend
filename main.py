import base64
import hashlib
from io import BytesIO
import os
import secrets
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException, Query, Request
import logging
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import requests
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from DB_Interface import login_user, register_user

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = FastAPI()

code_verifiers = {}  # Store code verifiers temporarily

# 1️⃣ **OAuth Login - Step 1**
@app.get("/auth/login")
async def login():
    """Start the OAuth login process with PKCE"""
    # Generate a unique code_verifier and code_challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    # Store the verifier temporarily
    code_verifiers[code_verifier] = True

    # Build the authorization URL for Google
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/fitness.activity.read",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    authorization_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    logging.info(f"Authorization URL: {authorization_url}")

    return {"login_url": authorization_url, "code_verifier": code_verifier}


# 2️⃣ **OAuth Callback - Step 2**
@app.get("/auth/callback")
async def callback(request: Request):
    """Handle the callback from Google and exchange authorization code for tokens"""
    query_params = request.query_params
    code = query_params.get("code")
    code_verifier = query_params.get("code_verifier")

    if not code or not code_verifier or code_verifier not in code_verifiers:
        raise HTTPException(status_code=400, detail="Invalid code verifier or code")

    try:
        # Exchange the authorization code for an access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        logging.info(f"Access token received: {token_data}")

        # Remove the used code_verifier
        del code_verifiers[code_verifier]

        return {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
        }
    except Exception as e:
        logging.error(f"Error during callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during callback: {str(e)}")


@app.get("/fit/data")
async def get_google_fit_data(access_token: str):
    """Fetch Google Fit data"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        body = {
            "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
            "bucketByTime": {"durationMillis": 86400000},  # 1 day
            "startTimeMillis": 1692316800000,  # Example start time (replace with actual)
            "endTimeMillis": 1692403200000    # Example end time (replace with actual)
        }

        response = requests.post(
            "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
            json=body,
            headers=headers
        )
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch Google Fit data: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to fetch fitness data")

        return response.json()
    except Exception as e:
        logging.error(f"Error fetching Fit data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching Fit data: {str(e)}")




@app.post("/register")
async def register(request: Request):
    try:
        user_data = await request.json()
        print("Received user data:", user_data)  # Debugging
        register_user(user_data)
        return {"message": "User registered successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.post("/login")
async def login(request: Request):
    user_data = await request.json()
    response = login_user(user_data)
    return response

@app.get("/test")
async def test():
    return {"Test": "Working"}
