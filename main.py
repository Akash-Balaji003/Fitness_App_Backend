import base64
from io import BytesIO
import os
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

flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI]
        }
    },
    scopes=["https://www.googleapis.com/auth/fitness.activity.read"]
)



@app.get("/auth/login")
async def login():
    """Start the OAuth login process"""
    logging.info("Starting login process")
    authorization_url, state = flow.authorization_url(prompt='consent')
    logging.info(f"Redirecting to: {authorization_url}")
    return {"login_url": authorization_url}


@app.get("/auth/callback")
async def callback(request: Request):
    """Handle the callback from Google OAuth"""
    try:
        # Get authorization code from URL
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="No code in callback URL")
        
        logging.info(f"Received authorization code: {code}")
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_in": credentials.expiry,
        }
    except Exception as e:
        logging.error(f"Error in callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error in callback: {str(e)}")


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
