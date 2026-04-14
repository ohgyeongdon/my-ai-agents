import os
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from search_news import search_sme_issues, search_youtube_issues

def safe_print(message):
    """Prints message safely to handle console encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('cp949', errors='replace').decode('cp949'))

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ASSETS_DIR = BASE_DIR / "assets"

# Configure Google GenAI (SDK v2)
client = genai.Client(api_key=GEMINI_API_KEY)

def get_system_instruction():
    """Reads the GEMS prompt from the markdown file."""
    prompt_path = BASE_DIR / "GEMS_Storyboard_Prompt_KR.md"
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "You are a specialized storyboard artist for 'zoSso_nyangz'."

def choose_topic():
    """Fetches news and YouTube issues and picks the most interesting one."""
    safe_print("[INFO] Searching for today's SME issues...")
    news_results = search_sme_issues()
    yt_results = search_youtube_issues()
    
    all_results = news_results + yt_results
    if not all_results:
        return "중소기업 상사의 황당한 갑질 해프닝"
        
    best_issue = all_results[0]
    safe_print(f"[SUCCESS] Selected Topic: {best_issue['title']}")
    return best_issue['title'] + "\n" + best_issue.get('snippet', '')

def generate_storyboard_scenario(topic):
    """Uses Gemini (Nano-Banana) to generate the 3-step scenario."""
    system_prompt = get_system_instruction()
    user_prompt = f"""
    당신은 '좆소냥즈' 스토리보드 작가입니다. 아래 지침을 엄격히 따라주세요.
    
    [시스템 지침]
    {system_prompt}
    
    [최신 이슈]
    {topic}
    
    위 이슈를 바탕으로 9개의 개별 컷(Scene)에 대한 상세한 '비주얼 프롬프트'를 생성해줘.
    결과는 반드시 각 컷별로 'Scene 1: [프롬프트]', 'Scene 2: [프롬프트]' 형식으로 작성해줘.
    """
    
    try:
        # Fixed: Using the confirmed Gemini 3 Flash model
        safe_print(f"[DEBUG] Calling model: gemini-3-flash-preview with topic: {topic[:50]}...")
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=user_prompt
        )
        if not response or not response.text:
            safe_print("[!] Empty response from Gemini.")
            return None
        return response.text
    except Exception as e:
        import traceback
        safe_print(f"[!] Error generating scenario: {e}")
        traceback.print_exc()
        return None

def generate_and_save_real_image(scene_prompt, folder_path, cut_index):
    """
    Imagen API를 사용하여 2K 해상도로 개별 이미지 생성 및 저장
    """
    # 2K 개별 컷을 위한 상세 프롬프트 구성
    image_prompt = f"""
    High-resolution 2K cinematic storyboard shot. 
    Style: Soft 3D Render, Felt / Wool Texture, Claymation-like aesthetic.
    Mood: Professional office lighting, realistic shadows, grayish corporate tones.
    Resolution: 2048x1152 (16:9).
    
    Characters:
    - Mujinyang: Chubby black & white cow-pattern cat, soft felt texture, blue eyes, white long-sleeve shirt, blue tie, flipped ID badge.
    - Butternyang: Chubby orange tabby cat, sleepy eyes, V-notch ear, white polo shirt, dark green utility vest.
    
    Scene Content:
    {scene_prompt}
    """
    
    models_to_try = [
        'imagen-4.0-ultra-generate-001', # 2K 지원 프리미엄 모델
        'imagen-4.0-generate-001',
        'imagen-3.0-generate-001'
    ]
    
    for model_name in models_to_try:
        try:
            safe_print(f"[*] Generating Cut {cut_index} using {model_name}...")
            
            # 2K Resolution configuration
            response = client.models.generate_images(
                model=model_name,
                prompt=image_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9", # 2048x1152
                    include_rai_reason=True,
                    output_mime_type="image/png"
                )
            )
            
            if response.generated_images:
                img_obj = response.generated_images[0]
                image_file = folder_path / f"cut_{cut_index:02d}.png"
                
                # SDK 응답 버전에 따른 이미지 데이터 추출
                if hasattr(img_obj, 'image_bytes') and img_obj.image_bytes:
                    data = img_obj.image_bytes
                elif hasattr(img_obj, 'image') and hasattr(img_obj.image, 'image_bytes'):
                    data = img_obj.image.image_bytes
                else:
                    data = img_obj.image # Binary direct fallback
                
                with open(image_file, "wb") as f:
                    f.write(data)
                
                safe_print(f"[SUCCESS] Cut {cut_index} saved: {image_file.name}")
                return True
                
        except Exception as e:
            safe_print(f"[!] {model_name} failed: {e}")
            continue
            
    return False

def run_mission():
    safe_print(f"\n[*] Mission Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not GEMINI_API_KEY:
        safe_print("[!] No GEMINI_API_KEY found in .env")
        return

    # 1. Choose Topic
    topic = choose_topic()
    
    # 2. Generate Scenario (Individual cut prompts)
    scenario_text = generate_storyboard_scenario(topic)
    if not scenario_text:
        safe_print("[!] MISSION ABORTED: Scenario generation failed.")
        return
    
    # 3. Create Folder
    date_str = datetime.now().strftime("%Y%m%d")
    folder_name = f"{date_str}_2K_Storyboard"
    folder_path = ASSETS_DIR / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    
    with open(folder_path / "scenario_log.md", "w", encoding="utf-8") as f:
        f.write(scenario_text)
        
    # 4. Parse scenes and generate 9 images
    safe_print("\n--- Generating 9 Individual 2K Cuts ---")
    
    # Simple parsing logic for 'Scene X:'
    scenes = []
    lines = scenario_text.split('\n')
    for line in lines:
        if 'Scene' in line and ':' in line:
            scenes.append(line.split(':', 1)[1].strip())
    
    # Fail-safe: if parsing failed, just use original lines or split by number
    if not scenes:
        scenes = [l.strip() for l in lines if l.strip()][:9]
        
    # Limit to 9 scenes
    scenes = scenes[:9]
    
    success_count = 0
    for i, scene_prompt in enumerate(scenes):
        if generate_and_save_real_image(scene_prompt, folder_path, i + 1):
            success_count += 1
            # Brief sleep to avoid rate limits if any
            time.sleep(1)
            
    if success_count > 0:
        safe_print(f"\n[DONE] Mission Complete! Generated {success_count}/9 high-res cuts.")
        safe_print(f"Folder: {folder_path}")
    else:
        safe_print("\n[!] Mission Failed: No images were generated.")

if __name__ == "__main__":
    run_mission()
