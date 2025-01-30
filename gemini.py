import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("Gemini API Key is missing!")
else:
    genai.configure(api_key=api_key)

# Generate text response
async def generate_response(query: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(query)
        return response.text
    except Exception as e:
        logger.error(f"Error in generating response: {e}")
        return "Sorry, I couldn't generate a response at the moment."

# Analyze image/file
async def analyze_image(file_path: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-pro-vision')
        response = await model.generate_content_async(["Describe this image.", file_path])
        return response.text
    except Exception as e:
        logger.error(f"Error in analyzing image: {e}")
        return "Sorry, I couldn't analyze the image at the moment."

# Extract text from PDF file
def extract_text_from_pdf(file_path: str) -> str:
    try:
        # Using PyPDF2 to extract text from PDF
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error in extracting text from PDF: {e}")
        return None

# Summarize text using Gemini
async def summarize_text(text: str) -> str:
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(f"Summarize this text: {text}")
        return response.text
    except Exception as e:
        logger.error(f"Error in summarizing text: {e}")
        return "Sorry, I couldn't summarize the text at the moment."

# Web search function
async def web_search(query: str) -> str:
    # Search query via an API (e.g., Google Search API, or use web scraping for a quick solution)
    search_url = f"https://www.google.com/search?q={query}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract top search results
        search_results = []
        for link in soup.find_all('a'):
            url = link.get('href')
            if "url?q=" in url:
                title = link.get_text()
                search_results.append(f"{title}: {url[7:]}")

        return "\n".join(search_results[:5]) if search_results else "No results found."
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        return "Sorry, I couldn't perform the web search at the moment."
