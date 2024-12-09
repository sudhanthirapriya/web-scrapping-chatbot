import os
from dotenv import load_dotenv
load_dotenv()

# Configuration file
API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMDB_URL = "./chroma_db" 
CHATLOG_URL = "db/chatbot.db"