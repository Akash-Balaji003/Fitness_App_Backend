import base64
import datetime
import hashlib
import json
import os
import secrets
from fastapi import FastAPI, HTTPException, Request
import logging
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
import requests
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timezone
from dotenv import load_dotenv

from DB_Interface import get_access_token, get_code_verifier, insert_code_verifier, insert_tokens, login_user, register_user

load_dotenv()

# Load environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = FastAPI()

# Session middleware to handle session storage for code_verifier
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.get("/auth/login")
async def login(request: Request, id: int):
    """Start the OAuth login process and generate a code verifier."""
    try:
        code_verifier = secrets.token_urlsafe(64)

        # Store the code_verifier in the database
        insert_code_verifier(code_verifier)

        logging.info(f"Stored code_verifier in DB: {code_verifier}")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        state = base64.urlsafe_b64encode(json.dumps({"id": id}).encode()).decode()

        login_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/fitness.activity.read+"
            f"https://www.googleapis.com/auth/fitness.heart_rate.read&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )

        logging.info(f"Generated Login URL: {login_url}")
        return {"login_url": login_url}
    except Exception as e:
        logging.error(f"❌ Error in /auth/login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in /auth/login: {str(e)}")


@app.get("/auth/callback")
async def callback(request: Request):
    """Handle the callback from Google and exchange code for tokens."""
    try:
        query_params = request.query_params
        code = query_params.get("code")

        state = request.query_params.get("state")
        if state:
            try:
                decoded_state = json.loads(base64.urlsafe_b64decode(state).decode())
                user_id = decoded_state.get("id")
                if not user_id:
                    logging.error("❌ Missing 'id' in decoded state")
                    raise HTTPException(status_code=400, detail="Missing 'id' in state")
                logging.info(f"✅ Received 'id' from state: {user_id}")
            except Exception as decode_error:
                logging.error(f"❌ Failed to decode state: {state}, Error: {decode_error}")
                raise HTTPException(status_code=400, detail="Invalid state format")
        else:
            logging.error("❌ Missing 'state' parameter")
            raise HTTPException(status_code=400, detail="Missing state parameter")


        # Retrieve code_verifier from DB
        code_verifier = get_code_verifier()
        logging.info(f"✅ Received 'code': {code}")
        logging.info(f"✅ Retrieved 'code_verifier': {code_verifier}")

        if not code or not code_verifier:
            logging.error("❌ Missing 'code' or 'code_verifier'")
            raise HTTPException(status_code=400, detail="Missing code or code_verifier")

        # Exchange the code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        response = requests.post(token_url, data=payload)
        token_data = response.json()

        if "access_token" in token_data:
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", "")
            logging.info(f"✅ Tokens received for user {user_id}: Access Token - {access_token}")

            # Store tokens in the database
            insert_tokens(user_id, access_token, refresh_token)

            # Redirect back to the app with tokens and ID
            app_redirect_url = (
                f"com.googleusercontent.apps.115771399305-civdip3bp5413g9r7v43q0vlbv74tvre://auth/callback?"
                f"code={code}&access_token={access_token}&refresh_token={refresh_token}&id={user_id}"
            )
            return RedirectResponse(url=app_redirect_url)
        else:
            logging.error(f"❌ Failed to fetch tokens: {token_data}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
    except Exception as e:
        logging.error(f"❌ Error in /auth/callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in /auth/callback: {str(e)}")

@app.get("/get/token")
async def get_token(id: int):
    token = get_access_token(id)
    return {"access_token": token}

@app.get("/fit/data")
async def get_google_fit_data(access_token: str):
    """Fetch Google Fit data"""
    start_time = int(datetime(2024, 12, 14, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    end_time = int(datetime(2024, 12, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    print(start_time, end_time)
    try:
        logging.info("Access Token: %s", access_token)
        headers = {'Authorization': f'Bearer {access_token}'}
        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.heart_rate.bpm"}
            ],
            "bucketByTime": {"durationMillis": 86400000},  # 1 day
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        logging.info("Sending request to Google Fit API with the following body: %s", body)

        response = requests.post(
            "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate",
            json=body,
            headers=headers
        )

        logging.info("Received response status code: %d", response.status_code)

        if response.status_code != 200:
            logging.error(f"Failed to fetch Google Fit data: {response.text}")
            raise HTTPException(status_code=400, detail=f"Failed to fetch fitness data: {response.text}")

        response_data = response.json()
        logging.info("Bucket data: %s", json.dumps(response_data.get('bucket', []), indent=4))

        logging.info("Successfully fetched fitness data: %s", response_data)

        return response_data
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
