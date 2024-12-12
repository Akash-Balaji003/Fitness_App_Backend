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
import httpx
from starlette.middleware.sessions import SessionMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from DB_Interface import login_user, register_user

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")

code_verifiers = {}  # Store code verifiers temporarily



@app.get("/auth/login")
async def login(request: Request):
    """Start the OAuth login process and generate a code verifier."""
    try:
        # Step 1: Generate the code_verifier and store it in the session
        code_verifier = secrets.token_urlsafe(64)
        request.session['code_verifier'] = code_verifier  # Store in session

        # Step 2: Create the code_challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        # Step 3: Generate the Google OAuth login URL
        login_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/fitness.activity.read&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256&"
            f"access_type=offline"
        )

        logging.info(f"🔑 Generated Code Verifier: {code_verifier}")
        logging.info(f"🔗 Login URL: {login_url}")

        return {"login_url": login_url}
    except Exception as e:
        logging.error(f"❌ Error in /auth/login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in /auth/login: {str(e)}")


@app.get("/auth/callback")
async def callback(request: Request):
    """Handle the callback from Google and exchange code for tokens."""
    try:
        # Step 1: Extract query params (code) and session data (code_verifier)
        query_params = request.query_params
        code = query_params.get("code")
        code_verifier = request.session.get('code_verifier')  # Get from session

        if not code or not code_verifier:
            logging.error(f"❌ Missing 'code' or 'code_verifier'")
            raise HTTPException(status_code=400, detail="Missing code or code_verifier")

        logging.info(f"✅ Received Code: {code}")
        logging.info(f"✅ Using Code Verifier: {code_verifier}")

        # Step 2: Exchange the code for tokens
        token_endpoint = "https://oauth2.googleapis.com/token"

        payload = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'code_verifier': code_verifier,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        async with httpx.AsyncClient() as client:
            response = await client.post(token_endpoint, data=payload, headers=headers)

        if response.status_code != 200:
            logging.error(f"❌ Failed to exchange token: {response.json()}")
            raise HTTPException(status_code=500, detail="Failed to exchange token with Google")

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        logging.info(f"✅ Access Token: {access_token}")
        logging.info(f"🔄 Refresh Token: {refresh_token}")

        # Remove code verifier from session
        del request.session['code_verifier']

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": token_data.get("expires_in"),
        }
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
