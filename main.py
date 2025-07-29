from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
import logging

from DB_Interface import generate_qr, get_all_users, post_feedback_to_db, check_account, fetch_activities, fetch_transactions, get_longest_streak, get_pending_friend_requests, get_total_steps_for_user, get_total_steps_previous_day, get_user_credit_balance, get_user_monthly_steps, get_weekly_statistics, insert_activity_data, insert_transaction_data, leaderboard_data, list_friends, login_user, register_user, respond_friend_request, search_users_by_name, send_friend_request, update_steps, update_user

app = FastAPI()

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.post("/", response_class=HTMLResponse)
async def fastapi_home():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """

@app.post("/register")
async def register(request: Request):
    try:
        user_data = await request.json()
        print("Received user data:", user_data)  # Debugging
        register_user(user_data)
        logging.info("Received user data : %s", user_data)  # Debugging
        return {"message": "User registered successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        logging.error("Received Error data : ", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.post("/login")
async def login(request: Request):
    user_data = await request.json()
    response = login_user(user_data)
    return response

@app.post("/update-steps")
async def stepCount(request: Request):
    step_data = await request.json()
    logging.info("%s, %s, %s, %s", step_data['user_id'], 
            step_data['date'], 
            step_data['steps'], 
            step_data['midnight_step_count'])
    update_steps(step_data)
    logging.info("Updated step data: %s", step_data)  # Debugging
    return {"status": "success", "message": "Steps updated successfully"}

@app.get("/test")
async def test():
    logging.info("Test...")  # Debugging
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
    logging.info("Get Activities for ID: %s", id)  # Debugging with proper formatting
    return fetch_activities(id)

@app.post("/update-user")
async def update_profile_endpoint(request: Request):
    try:
        user_data = await request.json()
        logging.info("Received profile data: ", user_data)  # Debugging
        
        result = update_user(user_data)
        
        return result
    
    except Exception as e:
        logging.error("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.get("/get-friends")
async def friendList(id: int):
    logging.info("Get Friends for ID: %s", id)  # Debugging with proper formatting
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

@app.get("/monthly-steps")
async def get_monthly_steps(id: int):
    """
    Endpoint to fetch monthly steps for a specific user_id, formatted as { "day": "steps" }.
    """
    try:
        # Fetch data from the database
        steps = get_user_monthly_steps(id)

        # Format the result into the desired format
        formatted_steps = {item["step_date"].split("-")[2]: item["total_steps"] for item in steps}

        # Ensure all days of the month are present with default 0 for missing days
        from datetime import datetime
        import calendar

        # Get the current year and month
        now = datetime.now()
        year = now.year
        month = now.month

        # Find the number of days in the current month
        _, num_days = calendar.monthrange(year, month)

        # Create a complete dictionary for the month
        complete_steps = {str(day): formatted_steps.get(str(day), 0) for day in range(1, num_days + 1)}

        return complete_steps

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/get-streaks")
async def Streaks(id: int):
    logging.info("Get Streaks for ID: %s", id)  # Debugging with proper formatting
    return get_longest_streak(id)

@app.get("/get-total-steps")
async def totalSteps(id: int):
    logging.info("Get Total Steps for ID: %s", id)  # Debugging with proper formatting
    return get_total_steps_for_user(id)

@app.get("/get-total-sensor-steps")
async def get_total_sensor_steps(id: int):
    logging.info("Get Total Sensor Steps for ID: %s", id)  # Debugging with proper formatting
    return get_total_steps_previous_day(id)

@app.post("/feedback")
async def post_feedback(request: Request):
    try:
        feedback = await request.json()
        post_feedback_to_db(feedback)

    except Exception as e:
        logging.error("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}") 

@app.post("/new-transaction")
async def register(request: Request):
    try:
        user_data = await request.json()
        print("Received user data:", user_data)  # Debugging
        insert_transaction_data(user_data)
        return {"message": "Transaction Noted successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")
    
@app.get("/get-transaction")
async def getTransaction(id: int):
    logging.info("Get Transaction for ID: %s", id)  # Debugging with proper formatting
    return fetch_transactions(id)

@app.get("/get-balance")
async def getBalance(id: int):
    logging.info("Get Balance for ID: %s", id)  # Debugging with proper formatting
    return get_user_credit_balance(id)

@app.get("/admin/get-users")
async def getUsers():
    try:
        users = get_all_users()  # Call the function to search users by name
        return users
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error searching users: {err}")
    
@app.get("/admin/search-users")
async def admin_search_users(query: str):
    try:
        users = search_users(query)  # Call the function to search users by name
        return users
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error searching users: {err}")
    
@app.post("/generate-qr")
async def generate_qr_endpoint(request: Request):
    try:
        body = await request.json()
        name = body.get("name")
        amount = body.get("amount")

        if not name or amount is None:
            raise ValueError("Missing 'name' or 'amount' in request body.")

        # Save to unique filename
        filename = f"{name}.png"
        generate_qr(name, amount, filename)

        return FileResponse(
            path=filename,
            filename=filename,
            media_type='image/png',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logging.error("QR Generation Error: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")
 
# Run the application with: uvicorn main:app --reload