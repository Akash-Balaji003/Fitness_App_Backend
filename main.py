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

@app.get("/auth/login")
async def login():
    """Start the OAuth login process and generate a code verifier."""
    try:
        code_verifier = secrets.token_urlsafe(64)
        code_verifiers[code_verifier] = True
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()
        
        logging.info(f"Generated Code Verifier: {code_verifier}")
        return {"login_url": "your_google_oauth_url_here", "code_verifier": code_verifier}
    except Exception as e:
        logging.error(f"❌ Error in /auth/login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in /auth/login: {str(e)}")


@app.get("/auth/callback")
async def callback(request: Request):
    """Handle the callback from Google and exchange code for tokens."""
    try:
        query_params = request.query_params
        code = query_params.get("code")
        code_verifier = query_params.get("code_verifier")

        if not code or not code_verifier:
            raise HTTPException(status_code=400, detail="Missing code or code_verifier")

        if code_verifier not in code_verifiers:
            logging.error(f"❌ Code verifier mismatch. Provided: {code_verifier}")
            raise HTTPException(status_code=400, detail="Invalid code verifier")

        logging.info(f"✅ Code: {code}, Verifier: {code_verifier}")
        
        # Exchange the code for tokens
        # Exchange logic here...

        del code_verifiers[code_verifier]
        return {"access_token": "mock_access_token"}
    except Exception as e:
        logging.error(f"❌ Error in /auth/callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in /auth/callback: {str(e)}")


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
