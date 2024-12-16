from datetime import datetime
import logging
from fastapi import HTTPException
import mysql.connector
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_db_connection():
    return mysql.connector.connect(
        host="fitness-database.mysql.database.azure.com",
        port=3306,
        username="akash",
        password="Akash003!",
        database="fitness"

    )

def hash_password(password: str):
    return pwd_context.hash(password)

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

def insert_code_verifier(code_verifier: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO codes (code_verifier) VALUES (%s)"
            cursor.execute(sql, (code_verifier,))
            connection.commit()
            logging.info(f"Stored code_verifier in DB: {code_verifier}")
    finally:
        connection.close()

# Function to retrieve the most recent code_verifier from the database
def get_code_verifier() -> str:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT code_verifier FROM codes ORDER BY created_at DESC LIMIT 1"
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                raise HTTPException(status_code=404, detail="Code verifier not found")
    finally:
        connection.close()

def insert_tokens(user_id: int, access_token: str, refresh_token: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Prepare SQL query to insert access_token and refresh_token
            sql = """
                INSERT INTO users (user_id, access_token, refresh_token, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    access_token = VALUES(access_token),
                    refresh_token = VALUES(refresh_token),
                    updated_at = VALUES(updated_at)
            """
            now = datetime.now()
            cursor.execute(sql, (user_id, access_token, refresh_token, now, now))
            connection.commit()
            logging.info(f"Stored access and refresh tokens for user {user_id}")
    finally:
        connection.close()

def get_access_token(user_id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Prepare SQL query to fetch the access token for the given user_id
            sql = "SELECT access_token FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result[0]  # Return the access token
            else:
                logging.warning(f"No access token found for user {user_id}")
                return None
    finally:
        connection.close()

def get_refresh_token(user_id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Prepare SQL query to fetch the refresh token for the given user_id
            sql = "SELECT refresh_token FROM users WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result[0]  # Return the refresh token
            else:
                logging.warning(f"No refresh token found for user {user_id}")
                return None
    finally:
        connection.close()