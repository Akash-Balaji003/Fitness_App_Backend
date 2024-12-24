from fastapi import FastAPI, HTTPException, Request
import logging

from DB_Interface import check_account, fetch_activities, get_pending_friend_requests, get_weekly_statistics, insert_activity_data, leaderboard_data, list_friends, login_user, register_user, respond_friend_request, search_users_by_name, send_friend_request, update_steps, update_user

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

@app.get("/get-friends")
async def friendList(id: int):
    return list_friends(id)

@app.get("/send-request")
async def sendRequest(req_id: int, rec_id: int):
    return send_friend_request(req_id, rec_id)

@app.get("/respond-request")
async def respondRequest(id: int, status: str):
    return respond_friend_request(id, status)

@app.get("/get-pending-requests")
async def getPending(id: int):
    return get_pending_friend_requests(id)

@app.get("/get-leaderboard")
async def leaderboardData(id: int):
    return leaderboard_data(id)

@app.get("/users/search/")
def search_users(name: str):
    try:
        users = search_users_by_name(name)  # Call the function to search users by name
        return users
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error searching users: {err}")

@app.post("/check-user")
async def checkAccount(request: Request):
    try:
        user_data = await request.json()
        logging.info("Received profile data:", user_data)  # Debugging
        result = check_account(user_data)
        return result
    
    except Exception as e:
        logging.error("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")
