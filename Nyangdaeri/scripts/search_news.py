import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_sme_issues(query="중소기업 실황 빌런 해프닝", num_results=5):
    """
    Search for SME-related issues using Serper API.
    """
    if not SERPER_API_KEY:
        print("Error: SERPER_API_KEY not found in .env")
        return []

    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "gl": "kr",
        "hl": "ko",
        "num": num_results
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        results = []
        # Process organic search results
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
                "type": "news"
            })
            
        return results
    except Exception as e:
        print(f"Error during news search: {e}")
        return []

def search_youtube_issues(query="중소기업 빌런 숏츠", num_results=5):
    """
    Search for SME-related YouTube videos using Serper API.
    """
    if not SERPER_API_KEY:
        return []

    url = "https://google.serper.dev/videos"
    payload = json.dumps({
        "q": query,
        "gl": "kr",
        "hl": "ko",
        "num": num_results
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("videos", []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
                "type": "youtube"
            })
        return results
    except Exception as e:
        print(f"Error during YouTube search: {e}")
        return []

if __name__ == "__main__":
    print("--- SME News Search Test ---")
    news = search_sme_issues()
    for n in news:
        print(f"[{n['type']}] {n['title']}")
        
    print("\n--- SME YouTube Search Test ---")
    yt = search_youtube_issues()
    for y in yt:
        print(f"[{y['type']}] {y['title']}")
