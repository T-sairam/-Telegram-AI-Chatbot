import os
import logging
import pymongo
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
from db import register_user, save_chat, save_file
from gemini import generate_response, analyze_image, extract_text_from_pdf, summarize_text, web_search

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB setup
uri = os.getenv("MONGO_URI")  # Mongo URI from .env
client = pymongo.MongoClient(uri)
db = client['telegram_bot']  # Database name (can be any name)
users_collection = db['users']  # Collection for users
chats_collection = db['chats']  # Collection for chat logs
files_collection = db['files']  # Collection for file data

# Create indexes for faster queries (optional but recommended)
users_collection.create_index("user_id", unique=True)
chats_collection.create_index("timestamp")
files_collection.create_index("timestamp")

# Start command
async def start(update: Update, context: CallbackContext):
    user = update.effective_user

    # Check if user is already registered in MongoDB
    if not users_collection.find_one({"user_id": user.id}):
        # Register the user (first interaction)
        register_user(user.id, user.first_name, user.username, None)

    # Create the contact sharing button
    contact_button = KeyboardButton("Share Contact", request_contact=True)
    
    # Send message asking for the phone number (after user registration)
    await update.message.reply_text(
        "Please share your phone number to proceed.",
        reply_markup=ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)
    )

# Handle contact sharing
async def handle_contact(update: Update, context: CallbackContext):
    user = update.effective_user
    phone_number = update.message.contact.phone_number

    # Update user's phone number in MongoDB
    register_user(user.id, user.first_name, user.username, phone_number)
    await update.message.reply_text("Thank you for sharing your contact!")

# Handle text messages
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_input = update.message.text

    # Check if user input is a number and handle it as a string to avoid scientific notation
    if user_input.isdigit():
        # Confirm the number entered by the user
        await update.message.reply_text(f"Thank you! You've entered the number: {user_input}")
    else:
        # Handle non-numeric input (e.g., for chat-based responses)
        response = await generate_response(user_input)
        save_chat(user_id, user_input, response)
        await update.message.reply_text(response)

# Handle image/file uploads
async def handle_document(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    file = await update.message.document.get_file()
    file_path = await file.download_to_drive()

    # Check if file is an image or a PDF
    if file.file_name.endswith(('jpg', 'jpeg', 'png')):
        description = await analyze_image(file_path)
    elif file.file_name.endswith('pdf'):
        # Extract text from PDF and summarize
        extracted_text = extract_text_from_pdf(file_path)
        if extracted_text:
            description = await summarize_text(extracted_text)
        else:
            description = "Failed to extract text from PDF."
    else:
        description = "Unsupported file format."

    # Save file analysis to MongoDB
    save_file(user_id, update.message.document.file_name, description)
    await update.message.reply_text(f"File analysis: {description}")

# Web search command
async def web_search(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query after /websearch.")
        return

    # Call the Gemini web search API
    search_results = await web_search(query)
    await update.message.reply_text(search_results)

# MongoDB Functions
def register_user(user_id, first_name, username, phone_number):
    """Register or update a user in the MongoDB."""
    user_data = {
        "user_id": user_id,
        "first_name": first_name,
        "username": username,
        "phone_number": phone_number,
        "registered_at": datetime.datetime.now()
    }
    users_collection.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

def save_chat(user_id, user_input, bot_response):
    """Save user chats in MongoDB."""
    chat_data = {
        "user_id": user_id,
        "user_input": user_input,
        "bot_response": bot_response,
        "timestamp": datetime.datetime.now()  # Use datetime.datetime.now() instead of pymongo.Timestamp
    }
    chats_collection.insert_one(chat_data)

def save_file(user_id, file_name, description):
    """Save file information and analysis in MongoDB."""
    file_data = {
        "user_id": user_id,
        "file_name": file_name,
        "description": description,
        "timestamp": datetime.datetime.now()  # Use datetime.datetime.now() instead of pymongo.Timestamp
    }
    files_collection.insert_one(file_data)

# Main function
def main():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CommandHandler("websearch", web_search))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()


