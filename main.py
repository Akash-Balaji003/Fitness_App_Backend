from fastapi import FastAPI, HTTPException, Request
import logging

from DB_Interface import fetch_activities, get_weekly_statistics, insert_activity_data, login_user, register_user, update_steps, update_user

app = FastAPI()

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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

@app.post("/update-steps")
async def stepCount(request: Request):
    step_data = await request.json()
    update_steps(step_data)
    return {"status": "success", "message": "Steps updated successfully"}

@app.get("/test")
async def test():
    return {"Test": "Working"}

@app.get("/weekly-steps")
async def weeklySteps(id: int):
    return get_weekly_statistics(id)

@app.post("/store-activity")
async def register(request: Request):
    try:
        user_data = await request.json()
        print("Received user data:", user_data)  # Debugging
        insert_activity_data(user_data)
        return {"message": "Activity Noted successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.get("/fetch-activities")
async def getActivites(id: int):
    return fetch_activities(id)

@app.post("/update-user")
async def update_profile_endpoint(request: Request):
    try:
        user_data = await request.json()
        logging.info("Received profile data:", user_data)  # Debugging
        
        result = update_user(user_data)
        
        return result
    
    except Exception as e:
        logging.error("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")
