import os
from google import genai
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path("c:/Users/iljoo/Desktop/Work/꼭하자/youtube_shorts_automation")
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

try:
    models = client.models.list()
    for m in models:
        print(f"Model: {m.name}")
except Exception as e:
    print(f"Error: {e}")
