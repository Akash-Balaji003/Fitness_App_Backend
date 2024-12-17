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
    
        # Insert or update steps for a user on a specific date
        query = """
        INSERT INTO Steps (user_id, date, steps)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE steps = VALUES(steps), updated_at = CURRENT_TIMESTAMP;
        """
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
        query_users = """INSERT INTO users (username, phone_number, email, DOB, height, weight, diet, password) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_users, (
            user_data['username'], 
            user_data['phone_number'], 
            user_data['email'], 
            user_data['DOB'], 
            user_data['height'], 
            user_data['weight'], 
            user_data['diet'],  # diet can be 'veg', 'non-veg', or 'vegan'
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
            SELECT user_id, password, username, phone_number, diet, height, weight, email
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
            "email": db_user['email']
        }

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error: {err}")
    
    finally:
        cursor.close()
        connection.close()
