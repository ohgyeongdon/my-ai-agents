import os
import json
import pickle
from pathlib import Path
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Define base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
ASSETS_DIR = BASE_DIR / "assets"

# 🐟 코다리 부장: "대표님, 유튜브 업로드 전담 로봇 '코다리-Uploader' 가동합니다!" 🫡🚀

# API 설정
CLIENT_SECRETS_FILE = str(BASE_DIR / "client_secrets.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
TOKEN_FILE = str(BASE_DIR / "config" / "token.pickle")

def get_authenticated_service():
    credentials = None
    # 기존 토큰 로드 (있을 경우)
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)
            
    # 유효한 인증 정보가 없으면 새로 인증
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
            
        # 토큰 저장
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
            
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def upload_video(video_path, title, description, tags, category_id="22", privacy_status="private"):
    youtube = get_authenticated_service()
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    
    print(f"Uploading file: {video_path}...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
            
    print(f"Upload complete! Video ID: {response['id']}")
    return response

if __name__ == "__main__":
    import sys
    
    ep_num = "001"
    if len(sys.argv) > 1:
        ep_num = sys.argv[1]

    config_file = SRC_DIR / f"shorts_script_{ep_num}.json"

    if not config_file.exists():
        print(f"Error: Config file {config_file} not found.")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Determine video file: use 'video_file' from config if present, else fallback
    if "video_file" in config and os.path.exists(config["video_file"]):
        video_file = config["video_file"]
    elif ep_num == "001":
        video_file = str(ASSETS_DIR / "zoSso_ep1.mp4")
    else:
        video_file = str(ASSETS_DIR / f"final_short_{ep_num}.mp4")

    if not os.path.exists(video_file):
        print(f"Error: Video file {video_file} not found.")
        sys.exit(1)

    print(f"Uploading EP{ep_num}: {config['title']}")
    upload_video(
        video_path=video_file,
        title=config["title"],
        description=config["description"],
        tags=config["tags"],
        privacy_status="public"
    )
