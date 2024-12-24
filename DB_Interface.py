from fastapi import HTTPException
import mysql.connector
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str):
    return pwd_context.hash(password)

def get_db_connection():
    return mysql.connector.connect(
        host="fitness-database.mysql.database.azure.com",
        port=3306,
        username="akash",
        password="Akash003!",
        database="fitness"

    )

def update_steps(step_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Insert into Users table with diet included
        query = """
        INSERT INTO Steps (user_id, date, steps)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE steps = VALUES(steps), updated_at = CURRENT_TIMESTAMP;
        """
        cursor.execute(query, (
            step_data['user_id'], 
            step_data['date'], 
            step_data['steps'], 
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
        # Insert into Users table with diet included
        query_users = """INSERT INTO users (username, phone_number, email, DOB, height, weight, diet, gender, experience, stepgoal, password) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_users, (
            user_data['username'], 
            user_data['phone_number'], 
            user_data['email'], 
            user_data['DOB'], 
            user_data['height'], 
            user_data['weight'], 
            user_data['diet'],
            user_data['gender'],
            user_data['experience'],
            user_data['stepgoal'],
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
            SELECT user_id, password, username, phone_number, diet, height, weight, email, gender, experience, stepgoal
            FROM Users
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
            "diet": db_user['diet'],
            "height": db_user['height'],
            "weight": db_user['weight'],
            "email": db_user['email'],
            "gender": db_user['gender'],
            "experience": db_user['experience'],
            "stepgoal": db_user['stepgoal']
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
                SUM(steps) AS total_steps
            FROM Steps
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
                                activity, duration, user_id
                              ) VALUES (%s, %s, %s)"""
        cursor.execute(query_activities, (
            activity_data['activity'],
            activity_data['duration'],
            activity_data['user_id']
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
        query = """SELECT activity_id, activity, duration 
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
        # Update the Users table with the provided data
        query = """
        UPDATE Users
        SET 
            height = %s,
            weight = %s,
            diet = %s,
            experience = %s,
            stepgoal = %s
        WHERE user_id = %s
        """
        cursor.execute(query, (
            user_data['height'],
            user_data['weight'],
            user_data['diet'],
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
        # Check if a friend request already exists
        query_check = """
        SELECT * FROM friendships 
        WHERE requester_id = %s AND recipient_id = %s
        """
        cursor.execute(query_check, (requester_id, recipient_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Friend request already sent.")

        # Insert the friend request
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
        SELECT users.user_id, users.username
        FROM friendships
        JOIN users ON 
            (users.user_id = friendships.requester_id AND friendships.recipient_id = %s) OR
            (users.user_id = friendships.recipient_id AND friendships.requester_id = %s)
        WHERE friendships.status = 'accepted'
        """
        
        cursor.execute(query, (user_id, user_id))
        friends = cursor.fetchall()

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
            COALESCE(steps.steps, 0) AS step_count
        FROM friendships
        JOIN users 
            ON (users.user_id = friendships.requester_id AND friendships.recipient_id = %s) 
            OR (users.user_id = friendships.recipient_id AND friendships.requester_id = %s)
        LEFT JOIN steps 
            ON steps.user_id = users.user_id 
            AND steps.date = CURDATE() - INTERVAL 2 DAY
        WHERE friendships.status = 'accepted'
        """
        
        cursor.execute(query, (user_id, user_id))
        friends = cursor.fetchall()

        return friends
    
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
