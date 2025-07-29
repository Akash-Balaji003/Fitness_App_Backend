import logging
from fastapi import HTTPException, Query
import mysql.connector
from passlib.context import CryptContext
from datetime import datetime, timedelta
import json
import qrcode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str):
    return pwd_context.hash(password)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        username="root",
        password="Akash003!",
        database="fitness"
    )

def update_steps(step_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        logging.info("[INSIDE UPDATE steps DB FUNC] Updated step data: %s", step_data)  # Debugging
        logging.info("[INSIDE UPDATE steps DB FUNC] Midnight step data: %s", step_data["midnight_step_count"])  # Debugging
        # Insert into users table with diet included
        query = """
        INSERT INTO steps (user_id, date, daily_step_count, midnight_step_count)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            daily_step_count = VALUES(daily_step_count), 
            midnight_step_count = VALUES(midnight_step_count), 
            updated_at = CURRENT_TIMESTAMP;
        """
        cursor.execute(query, (
            step_data['user_id'], 
            step_data['date'], 
            step_data['steps'], 
            step_data['midnight_step_count'] # Check this properly
        ))
        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def register_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Hash the password before storing it
    hashed_password = hash_password(user_data['password'])

    try:
        # Insert into users table with diet included
        query_users = """INSERT INTO users (username, phone_number, email, DOB, height, weight, blood_group, gender, experience, stepgoal, caloriegoal, password) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_users, (
            user_data['username'], 
            user_data['phone_number'], 
            user_data['email'], 
            user_data['DOB'], 
            user_data['height'], 
            user_data['weight'], 
            user_data['blood'],
            user_data['gender'],
            user_data['experience'],
            user_data['stepgoal'],
            user_data['caloriegoal'],
            hashed_password
        ))
        connection.commit()
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def login_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Fetch results as dictionary

    try:
        # Check if user exists and retrieve details
        query = """
            SELECT user_id, password, username, phone_number, height, weight, email, gender, experience, stepgoal, blood_group, DOB, caloriegoal
            FROM users
            WHERE phone_number = %s
        """
        cursor.execute(query, (user_data['phone_number'],))
        db_user_profiles = cursor.fetchall()

        # Check if user exists
        if not db_user_profiles:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        db_user = db_user_profiles[0]  # There should be one matching user

        # Check if the password matches
        if not verify_password(user_data['password'], db_user['password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Return user details without the password
        return {
            "user_id": db_user['user_id'],
            "username": db_user['username'],
            "phone_number": db_user['phone_number'],
            "height": db_user['height'],
            "weight": db_user['weight'],
            "email": db_user['email'],
            "gender": db_user['gender'],
            "experience": db_user['experience'],
            "stepgoal": db_user['stepgoal'],
            "blood_group": db_user['blood_group'],
            "DOB": db_user['DOB'],
            "caloriegoal": db_user['caloriegoal']
        }

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_weekly_statistics(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                DATE(date) AS day,
                SUM(daily_step_count) AS total_steps
            FROM steps
            WHERE 
                user_id = %s AND 
                date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY day
            ORDER BY day ASC;
        """, (user_id,))
        weekly_data = cursor.fetchall()

        # Format data for the frontend
        labels = [entry['day'].strftime('%a') for entry in weekly_data]  # Days of the week (e.g., Mon, Tue)
        steps = [entry['total_steps'] for entry in weekly_data]

        return {
            "labels": labels,
            "steps": steps,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly statistics: {str(e)}")
    finally:
        cursor.close()
        connection.close()

def insert_activity_data(activity_data: dict):
    connection = get_db_connection()  # Replace with your DB connection function
    cursor = connection.cursor()

    try:
        # Insert into activities table
        query_activities = """INSERT INTO activities (
                                activity, duration, user_id, activity_date
                              ) VALUES (%s, %s, %s, %s)"""
        cursor.execute(query_activities, (
            activity_data['activity'],
            activity_data['duration'],
            activity_data['user_id'],
            activity_data['activity_date']
        ))
        
        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def fetch_activities(user_id: int):
    connection = get_db_connection()  # Replace with your DB connection function
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch activities for a specific user_id
        query = """SELECT activity_id, activity, duration, activity_date
                   FROM activities 
                   WHERE user_id = %s"""
        cursor.execute(query, (user_id,))
        activities = cursor.fetchall()

        return activities

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def update_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Update the users table with the provided data
        query = """
        UPDATE users
        SET 
            height = %s,
            weight = %s,
            blood_group = %s,
            experience = %s,
            stepgoal = %s
        WHERE user_id = %s
        """
        cursor.execute(query, (
            user_data['height'],
            user_data['weight'],
            user_data['blood'],
            user_data['experience'],
            user_data['stepgoal'],
            user_data['user_id']  # Using user_id as the identifier
        ))

        connection.commit()
        return {"message": "Updated the user data successfully"}
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def send_friend_request(requester_id: int, recipient_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if a reciprocal friend request exists
        query_check_reciprocal = """
        SELECT status FROM friendships 
        WHERE requester_id = %s AND recipient_id = %s
        """
        cursor.execute(query_check_reciprocal, (recipient_id, requester_id))
        reciprocal_result = cursor.fetchone()

        if reciprocal_result:
            reciprocal_status = reciprocal_result[0]
            if reciprocal_status == "pending":
                raise HTTPException(status_code=400, detail="This user has already sent you a friend request.")

        # Check if a friend request already exists
        query_check = """
        SELECT status FROM friendships 
        WHERE requester_id = %s AND recipient_id = %s
        """
        cursor.execute(query_check, (requester_id, recipient_id))
        result = cursor.fetchone()

        if result:
            status = result[0]
            if status == "pending":
                raise HTTPException(status_code=400, detail="Friend request already sent.")
            elif status == "accepted":
                raise HTTPException(status_code=400, detail="You are already friends.")
            elif status == "rejected":
                # Update the status to pending
                query_update = """
                UPDATE friendships 
                SET status = 'pending'
                WHERE requester_id = %s AND recipient_id = %s
                """
                cursor.execute(query_update, (requester_id, recipient_id))
                connection.commit()
                return {"message": "Friend request sent successfully!"}
        else:
            # Insert a new friend request
            query_insert = """
            INSERT INTO friendships (requester_id, recipient_id, status)
            VALUES (%s, %s, 'pending')
            """
            cursor.execute(query_insert, (requester_id, recipient_id))
            connection.commit()
            return {"message": "Friend request sent successfully!"}
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def respond_friend_request(friendship_id: int, status: str):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if status not in ["accepted", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status.")

        # Update the friendship status
        query_update = """
        UPDATE friendships 
        SET status = %s 
        WHERE friend_id = %s
        """
        cursor.execute(query_update, (status, friendship_id))
        connection.commit()

        return {"message": f"Friend request {status} successfully!"}
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def list_friends(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch friends for the given user ID
        query = """
        SELECT users.user_id, users.username, friend_id
        FROM friendships
        JOIN users ON 
            (users.user_id = friendships.requester_id AND friendships.recipient_id = %s) OR
            (users.user_id = friendships.recipient_id AND friendships.requester_id = %s)
        WHERE friendships.status = 'accepted'
        """
        
        cursor.execute(query, (user_id, user_id))
        friends = cursor.fetchall()

        print (friends)
        
        return friends
    
    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def leaderboard_data(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch friends and their step count for the previous day
        query = """
        SELECT 
            users.user_id, 
            users.username, 
            COALESCE(steps.daily_step_count, 0) AS step_count
        FROM friendships
        JOIN users 
            ON (users.user_id = friendships.requester_id AND friendships.recipient_id = %s) 
            OR (users.user_id = friendships.recipient_id AND friendships.requester_id = %s)
        LEFT JOIN steps 
            ON steps.user_id = users.user_id 
            AND steps.date = CURDATE() - INTERVAL 1 DAY
        WHERE friendships.status = 'accepted'

        UNION ALL

        SELECT 
            %s AS user_id, 
            users.username, 
            COALESCE(steps.daily_step_count, 0) AS step_count
        FROM users
        LEFT JOIN steps
            ON steps.user_id = users.user_id 
            AND steps.date = CURDATE() - INTERVAL 1 DAY
        WHERE users.user_id = %s
        """
        
        cursor.execute(query, (user_id, user_id, user_id, user_id))
        leaderboard = cursor.fetchall()

        # Update the username for the current user
        for entry in leaderboard:
            if entry['user_id'] == user_id:
                entry['username'] = 'You'

        return leaderboard
    
    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_pending_friend_requests(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch pending friend requests where the user is the recipient
        query = """
        SELECT friendships.friend_id AS friendship_id, 
               users.user_id AS requester_id, 
               users.username AS requester_name, 
               users.email AS requester_email
        FROM friendships
        JOIN users ON users.user_id = friendships.requester_id
        WHERE friendships.recipient_id = %s AND friendships.status = 'pending'
        """
        cursor.execute(query, (user_id,))
        pending_requests = cursor.fetchall()

        return pending_requests

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def search_users_by_name(name: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Query to search for users whose names match the search query
        query = """
        SELECT user_id, username
        FROM users
        WHERE username LIKE %s
        """
        
        cursor.execute(query, (f"%{name}%",))  # Perform case-insensitive search using LIKE
        users = cursor.fetchall()

        return users
    
    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def check_account(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Check for existing account based on phone number or email
        query = """
        SELECT phone_number, email
        FROM users
        WHERE phone_number = %s OR email = %s
        """
        cursor.execute(query, (
            user_data['phone_number'],
            user_data['email']
        ))
        
        existing_user = cursor.fetchone()

        if existing_user:
            return {"message": "This number or email already has an account"}

        return {"message": "No account exists with the provided phone number or email."}
    
    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_user_monthly_steps(user_id: int):
    """
    Fetch all steps for a specific user_id grouped by date for the current month.
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for easy result handling

    try:
        # Query to fetch steps for the current month grouped by date
        query = """
        SELECT 
            DATE(date) AS step_date, 
            SUM(daily_step_count) AS total_steps
        FROM 
            steps
        WHERE 
            user_id = %s
            AND MONTH(date) = MONTH(CURRENT_DATE())
            AND YEAR(date) = YEAR(CURRENT_DATE())
        GROUP BY 
            DATE(date)
        ORDER BY 
            step_date;
        """
        cursor.execute(query, (user_id,))
        steps_data = cursor.fetchall()

        # Convert Decimal to int and format the step_date
        formatted_data = [
            {
                "step_date": item["step_date"].strftime("%Y-%m-%d"),
                "total_steps": int(item["total_steps"])
            }
            for item in steps_data
        ]

        return formatted_data

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_longest_streak(user_id: int):
    """
    Calculate the longest streak of steps greater than 1000 for a specific user_id.
    """
    connection = get_db_connection()  # Assuming this function is defined to get DB connection
    cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for easy result handling

    try:
        # SQL query to calculate the longest streak of steps greater than 1000
        query = """
        WITH streaks AS (
            SELECT
                date,
                daily_step_count,
                ROW_NUMBER() OVER (ORDER BY date) -
                ROW_NUMBER() OVER (PARTITION BY (daily_step_count > 1000) ORDER BY date) AS streak_group
            FROM steps
            WHERE daily_step_count > 1000
              AND user_id = %s
        )
        SELECT
            MAX(streak_length) AS longest_streak
        FROM (
            SELECT
                streak_group,
                COUNT(*) AS streak_length
            FROM streaks
            GROUP BY streak_group
        ) AS streak_lengths;
        """
        
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        # Return the longest streak or 0 if no result
        return result["longest_streak"] if result["longest_streak"] is not None else 0

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_total_steps_for_user(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Query to select the total sum of steps for the specific user_id
        query = """
        SELECT SUM(daily_step_count) AS total_steps
        FROM steps
        WHERE user_id = %s;
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()  # Fetch the single result

        if result is None or result[0] is None:
            raise HTTPException(status_code=404, detail="No step data found for the given user_id")

        return {"total_steps": result[0]}  # Access the value by index

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_total_steps_previous_day(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Calculate the previous day's date
        previous_day = (datetime.now() - timedelta(days=1)).date()
        print("Previous Day: ", previous_day)

        # Query to fetch the total_steps for the previous day
        query = """
        SELECT midnight_step_count
        FROM steps
        WHERE user_id = %s AND date = %s;
        """
        cursor.execute(query, (user_id, previous_day))
        result = cursor.fetchone()  # Fetch the single result

        print("Result: ", result)

        if result is None:
            raise HTTPException(status_code=404, detail="No step data found for the previous day")
        if result[0] is None:
            return {"total_steps": 0}

        return {"total_steps": result[0]}  # Return the value

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def post_feedback_to_db(feedback):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        logging.info("[INSIDE UPDATE FEEDBACK DB FUNC] Updated step data: %s", feedback)  # Debugging
        # Insert into users table with diet included
        query = """
        INSERT INTO feedback (user_id, description)
        VALUES (%s, %s)
        """
        cursor.execute(query, (
            feedback["user_id"],
            feedback["description"]
        ))
        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def insert_transaction_data(transaction_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO transactions (
                user_id, transaction_type, activity_type, amount
            ) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            transaction_data['user_id'],
            transaction_data['transaction_type'],
            transaction_data['activity_type'],
            transaction_data['amount']
        ))

        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def fetch_transactions(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT transaction_id, transaction_type, activity_type, amount, created_at
            FROM transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id,))
        transactions = cursor.fetchall()

        print(transactions)  # Debugging output
        return transactions

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def get_user_credit_balance(user_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # So we get column names in result

    try:
        query = """
            SELECT user_id, credit_balance
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return float(user['credit_balance'])

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

# Admin functionalities
def get_all_users():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                user_id,
                username,
                phone_number,
                email,
                DOB,
                height,
                weight,
                gender,
                blood_group,
                credit_balance
            FROM users
            """
        cursor.execute(query)
        users = cursor.fetchall()
        print(users)
        return users
    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    finally:
        cursor.close()
        connection.close()

def search_users(query: str = Query(..., min_length=1)):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        sql_query = """
            SELECT 
                user_id,
                username,
                phone_number,
                email,
                DOB,
                height,
                weight,
                gender,
                blood_group,
                credit_balance
            FROM users
            WHERE username LIKE %s
        """
        like_pattern = f"%{query}%"
        cursor.execute(sql_query, (like_pattern,))
        users = cursor.fetchall()
        print(users)  # Debugging output
        return users

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def generate_qr(Name, amount, filename):
    # Validate inputs (optional)
    if not isinstance(amount, (int, float)):
        raise ValueError("Amount must be a number")

    # Create a dictionary of data
    qr_data = {
        "name": Name,
        "transaction_type": "spend",
        "activity_type": "redeem",
        "amount": amount
    }

    # Convert dictionary to JSON string
    json_string = json.dumps(qr_data)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(json_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"QR code saved as {filename}")
