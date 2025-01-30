import os 
import logging
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["telegram_bot"]
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Create indexes for faster querying (optional but recommended)
try:
    db.users.create_index("user_id", unique=True)  # Unique index for user_id
    db.chats.create_index("timestamp")  # Index on timestamp for chat queries
    db.files.create_index("timestamp")  # Index on timestamp for file queries
    logger.info("Indexes created successfully.")
except Exception as e:
    logger.error(f"Failed to create indexes: {e}")

# Register user
def register_user(user_id: int, first_name: str, username: str, phone: str):
    try:
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "first_name": first_name,
                "username": username,
                "phone_number": phone,  # This will be updated later if user shares their contact
                "registered_at": datetime.now()
            }},
            upsert=True
        )
        logger.info(f"User {user_id} registered/updated successfully.")
    except Exception as e:
        logger.error(f"Error registering user {user_id}: {e}")

# Save chat history
def save_chat(user_id: int, query: str, response: str):
    try:
        db.chats.insert_one({
            "user_id": user_id,
            "query": query,
            "response": response,
            "timestamp": datetime.now()
        })
        logger.info(f"Chat saved for user {user_id}.")
    except Exception as e:
        logger.error(f"Error saving chat for user {user_id}: {e}")

# Save file metadata
def save_file(user_id: int, filename: str, description: str):
    try:
        db.files.insert_one({
            "user_id": user_id,
            "filename": filename,
            "description": description,
            "timestamp": datetime.now()
        })
        logger.info(f"File {filename} saved for user {user_id}.")
    except Exception as e:
        logger.error(f"Error saving file {filename} for user {user_id}: {e}")