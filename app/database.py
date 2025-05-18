import mysql.connector
from mysql.connector import Error
import os
import dotenv
import csv
import time
import logging
from typing import Optional, List, Dict, Any
import uuid
import bcrypt

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    pass

def get_db_connection(max_retries: int = 12, retry_delay: int = 5) -> mysql.connector.MySQLConnection:
    connection = None
    attempt = 1
    last_error = None

    while attempt <= max_retries:
        try:
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
                port=int(os.getenv("MYSQL_PORT")) if os.getenv("MYSQL_PORT") else 3306,
                ssl_ca=os.getenv("MYSQL_SSL_CA"),
                ssl_verify_cert=False
            )
            connection.ping(reconnect=True, attempts=1, delay=0)
            logger.info("Database connection established successfully")
            return connection
        except Error as err:
            last_error = err
            logger.warning(f"Connection attempt {attempt}/{max_retries} failed: {err}. Retrying in {retry_delay} seconds...")
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
            if attempt == max_retries:
                break
            time.sleep(retry_delay)
            attempt += 1
    raise DatabaseConnectionError(f"Failed to connect to database after {max_retries} attempts. Last error: {last_error}")

def drop_all_tables():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`")  # Use backticks for safety
            logger.info(f"Dropped table: {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
        logger.info("All tables dropped successfully")
    except Error as e:
        connection.rollback()
        logger.error(f"Error dropping tables: {e}")
    finally:
        cursor.close()
        connection.close()

def setup_database(drop_existing=False, create_sample_data=True):
    if drop_existing:
        drop_all_tables()

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(60) NOT NULL,
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Users table created or verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        logger.info("Sessions table created or verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                device_name VARCHAR(255) NOT NULL,
                device_type VARCHAR(255) NOT NULL,
                mac_address VARCHAR(17) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        logger.info("Devices table created or verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wardrobe (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                item_name VARCHAR(255) NOT NULL,
                item_type VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        logger.info("Wardrobe table created or verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temperature (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mac_address VARCHAR(17) NOT NULL,
                timestamp VARCHAR(255),
                value FLOAT,
                unit VARCHAR(50)
            );
        """)
        logger.info("Temperature table created or verified")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pressure (
                id INT AUTO_INCREMENT PRIMARY KEY,
                mac_address VARCHAR(17) NOT NULL,
                timestamp VARCHAR(255),
                value FLOAT,
                unit VARCHAR(50)
            );
        """)
        logger.info("Pressure table created or verified")

       

        connection.commit()
    except Error as e:
        connection.rollback()
        logger.error(f"Error setting up database tables: {e}")
        raise
    finally:
        cursor.close()
        connection.close()

def create_and_fill_tables():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        def insert_data_from_csv(file_path, table_name):
            try:
                with open(file_path, mode='r') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    for row in reader:
                        cursor.execute(
                            f"INSERT INTO {table_name} (timestamp, value, unit) VALUES (%s, %s, %s)",
                            row
                        )
                connection.commit()
                logger.info(f"Sample data inserted into {table_name} from {file_path}")
            except FileNotFoundError:
                logger.warning(f"Sample data file not found: {file_path}")
            except Error as e:
                logger.error(f"Error inserting sample data into {table_name}: {e}")
                connection.rollback()

    finally:
        cursor.close()
        connection.close()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_user_by_email(email: str) -> Optional[dict]:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

def create_user(username: str, password: str, location: str) -> Optional[str]:
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        user_id = generate_uuid()
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        cursor.execute(
            "INSERT INTO users (id, username, password, location) VALUES (%s, %s, %s, %s)",
            (user_id, username, hashed_password.decode('utf-8'), location)
        )
        connection.commit()
        return user_id
    except mysql.connector.IntegrityError:
        return None
    finally:
        cursor.close()
        connection.close()

def create_session(user_id: str) -> Optional[str]:
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        session_id = generate_uuid()
        cursor.execute("INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id))
        connection.commit()
        return session_id
    except Error as e:
        logger.error(f"Error creating session: {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()

def get_session(session_id: str) -> Optional[dict]:
    if not session_id:
        return None
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
    session = cursor.fetchone()
    cursor.close()
    connection.close()
    return session

def delete_session(session_id: str) -> bool:
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting session: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def register_device(user_id: str, device_name: str, device_type: str, mac_address: str) -> Optional[str]:
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        device_id = generate_uuid()
        cursor.execute(
            "INSERT INTO devices (id, user_id, device_name, device_type, mac_address) VALUES (%s, %s, %s, %s, %s)",
            (device_id, user_id, device_name, device_type, mac_address)
        )
        connection.commit()
        logger.info(f"Device registered successfully: {device_id}")
        return device_id
    except Error as e:
        logger.error(f"Error registering device: {e}")
        connection.rollback()
        return None
    finally:
        cursor.close()
        connection.close()

def get_user_by_id(user_id: str) -> Optional[dict]:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    except Error as e:
        logger.error(f"Error getting user by ID: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def get_user_devices(user_id: str) -> List[Dict[str, Any]]:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM devices WHERE user_id = %s", (user_id,))
        devices = cursor.fetchall()
        return devices if devices else []
    except Error as e:
        logger.error(f"Error getting devices for user {user_id}: {e}")
        return []
    finally:
        cursor.close()
        connection.close()