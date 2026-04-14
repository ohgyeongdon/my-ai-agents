import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, concatenate_audioclips
from moviepy.video import fx as vfx
from moviepy.audio import fx as afx
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Define base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
ASSETS_DIR = BASE_DIR / "assets"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Solar Planning Manager & Kodari Dev Manager: zoSso_nyangz Ep 001 Final Build!

def generate_elevenlabs_tts(text, character, output_path):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return False
    
    # 🐱 Character Voice Mapping
    voice_ids = {
        "Uzzanyang": "EXAVITQu4vr4xnSDxMaL", # Bella (Anxious/High)
        "Beotyeonyang": "pNInz6obpgmqS94M99p0" # Adam (Mature/Deep)
    }
    voice_id = voice_ids.get(character, "EXAVITQu4vr4xnSDxMaL")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(output_path, "wb") as f: f.write(response.content)
        return True
    return False

def create_subtitle_image(text, font_path, font_size=70, stroke_width=5):
    """Creates a tightly cropped RGBA image of the text with a stroke."""
    try: font = ImageFont.truetype(font_path, font_size)
    except: font = ImageFont.load_default()
        
    # Get text size for tight cropping
    dummy_img = Image.new('RGBA', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    left, top, right, bottom = bbox
    text_w, text_h = right - left, bottom - top
    
    # Add padding for stroke
    pad = stroke_width + 10
    img_w, img_h = text_w + 2*pad, text_h + 2*pad
    img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate drawing position to align text properly
    draw_pos = (pad - left, pad - top)
    
    # Draw thicker stroke (Multiple offsets for completeness)
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx*dx + dy*dy <= stroke_width*stroke_width:
                draw.text((draw_pos[0] + dx, draw_pos[1] + dy), text, font=font, fill=(0, 0, 0))
    
    draw.text(draw_pos, text, font=font, fill=(255, 255, 255))
    return np.array(img)

def assemble(script_name="shorts_script_003.json", scene_files=None, output_name=None):
    script_path = SRC_DIR / script_name
    if not script_path.exists():
        print(f"Error: Script {script_path} not found.")
        return

    with open(script_path, "r", encoding="utf-8") as f: script = json.load(f)

    # Resolve scene files and output name
    if scene_files is None:
        scene_files = script.get("scene_files", [])
    
    # Convert relative paths to absolute if needed
    scene_files = [str(ASSETS_DIR / Path(s).name) if not os.path.isabs(s) else s for s in scene_files]
    
    if output_name is None:
        v_file = script.get("video_file", "final_short.mp4")
        output_name = str(ASSETS_DIR / Path(v_file).name)

    voice_parts = script.get("voiceover_parts", [])
    subtitles = script.get("subtitles", [])
    target_duration = float(script.get("target_duration", 18.0))
    
    # 1. Multi-Voice Audio Generation
    print("Step 1: Generating Multi-Voice Narration...")
    audio_clips = []
    for i, part in enumerate(voice_parts):
        # Use absolute ASSETS_DIR for consistency
        temp_path = str(ASSETS_DIR / f"temp_p{i}.mp3")
        print(f"  - Generating audio for {part['character']}...")
        if not generate_elevenlabs_tts(part['text'], part['character'], temp_path):
            print(f"    [Warning] ElevenLabs failed for {part['character']}, falling back to gTTS.")
            tts = gTTS(text=part['text'], lang='ko'); tts.save(temp_path)
        audio_clips.append(AudioFileClip(temp_path))
        
    if audio_clips:
        final_audio = concatenate_audioclips(audio_clips)
        # Pad with silence if shorter than target, or clip if longer
        if final_audio.duration < target_duration:
            print(f"  - Padding audio to match target duration ({target_duration}s)")
            final_audio = final_audio.with_duration(target_duration)
        else:
            final_audio = final_audio.subclipped(0, target_duration)
    else:
        # Fallback to silence if no audio generated
        from moviepy.audio.AudioClip import AudioArrayClip
        final_audio = AudioArrayClip(np.zeros((int(44100*target_duration), 2)), fps=44100)

    # 2. Process Video Scenes
    print(f"Step 2: Processing {len(scene_files)} Scenes...")
    video_clips = []
    dur_per_scene = target_duration / max(len(scene_files), 1)
    TARGET_W, TARGET_H = 1080, 1920
    
    for s_file in scene_files:
        if os.path.exists(s_file):
            if s_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                clip = ImageClip(s_file).with_duration(dur_per_scene)
            else:
                clip = VideoFileClip(s_file)
            
            # 🔴 강제 9:16 크롭 (Shorts 규격 보장)
            orig_w, orig_h = clip.w, clip.h
            scale = max(TARGET_W / int(orig_w), TARGET_H / int(orig_h))
            clip = clip.resized(height=int(orig_h * scale)) if orig_w * scale >= TARGET_W else clip.resized(width=int(orig_w * scale))
            
            x_center = clip.w / 2
            y_center = clip.h / 2
            clip = clip.cropped(x_center=x_center, y_center=y_center, width=TARGET_W, height=TARGET_H)
            
            if clip.duration is None or clip.duration < dur_per_scene:
                clip = clip.with_duration(dur_per_scene)
            elif clip.duration > dur_per_scene:
                clip = clip.subclipped(0, dur_per_scene)
                
            video_clips.append(clip)

            
    if not video_clips:
        print("Error: No valid video scenes found.")
        return

    # Use 'chain' for efficiency since all clips are identical size
    final_video = concatenate_videoclips(video_clips, method="chain").with_audio(final_audio)
    
    # 3. Add Subtitles (Optimized Rendering)
    print("Step 3: Adding Optimized Subtitles...")
    composite_list = [final_video]
    
    # Font path search
    font_paths = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "C:/Windows/Fonts/arial.ttf"
    ]
    font_path = next((p for p in font_paths if os.path.exists(p)), "arial.ttf")

    for sub in subtitles:
        start, end, text = sub.get("start_time"), sub.get("end_time"), sub.get("text")
        if not text: continue
        
        # Create small text image
        sub_img = create_subtitle_image(text, font_path, font_size=80)
        
        # Primary Subtitle clip (Lower third - standard for shorts)
        sub_clip = (ImageClip(sub_img)
                    .with_start(start)
                    .with_duration(end-start)
                    .with_position(('center', 1450)))
        composite_list.append(sub_clip)
        
    # 4. Final Render
    print("Step 4: Finalizing and Rendering...")
    result = CompositeVideoClip(composite_list)
    result.write_videofile(output_name, fps=30, codec="libx264", audio_codec="aac")
    
    # Cleanup
    print("Step 5: Cleaning up temporary files...")
    for clip in audio_clips: clip.close()
    for i in range(len(voice_parts)): 
        path = ASSETS_DIR / f"temp_p{i}.mp3"
        if path.exists(): 
            try: os.remove(path)
            except: pass
    print(f"\nMission Success! Final video at: {output_name}")

if __name__ == "__main__":
    import sys
    target_script = sys.argv[1] if len(sys.argv) > 1 else "shorts_script_003.json"
    assemble(script_name=target_script)
