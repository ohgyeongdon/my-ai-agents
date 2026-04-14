import os
import requests
from pathlib import Path
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, CompositeVideoClip, ColorClip
from moviepy.audio import fx as afx

# Paths
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
SUBWAY_DIR = ASSETS_DIR / "subway"
SFX_DIR = ASSETS_DIR / "sfx"
SFX_DIR.mkdir(exist_ok=True)

# Frames
frames = [SUBWAY_DIR / f"subway_{i}.png" for i in range(1, 10)]

# Durations (Seconds)
durations = [1.0, 1.0, 1.0, 0.8, 1.2, 0.8, 1.2, 1.5, 2.5]

# SFX URLs (Royalty Free Placeholders/Direct Links)
SFX_SOURCES = {
    "ambient": "https://www.soundjay.com/transportation/subway-train-interior-1.mp3",
    "door_beep": "https://www.soundjay.com/buttons/beep-07.mp3",
    "shock": "https://www.soundjay.com/human/man-gasp-01.mp3",
    "train_move": "https://www.soundjay.com/transportation/train-passing-1.mp3",
    "boing": "https://www.soundjay.com/toy/toy-spring-1.mp3"
}

def download_sfx():
    print("Step 1: Downloading SFX...")
    downloaded = {}
    for name, url in SFX_SOURCES.items():
        path = SFX_DIR / f"{name}.mp3"
        if not path.exists():
            print(f"  - Downloading {name}...")
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(path, "wb") as f: f.write(r.content)
                    downloaded[name] = str(path)
                else:
                    print(f"    [!] Failed to download {name} (Status: {r.status_code})")
            except Exception as e:
                print(f"    [!] Error downloading {name}: {e}")
        else:
            downloaded[name] = str(path)
    return downloaded

def assemble_subway():
    sfx = download_sfx()
    
    print("Step 2: Creating Image Clips...")
    clips = []
    current_time = 0
    audio_clips = []
    
    # Target Resolution (Shorts)
    TARGET_W, TARGET_H = 1080, 1920
    
    for i, (f_path, dur) in enumerate(zip(frames, durations)):
        if not f_path.exists():
            print(f"Error: {f_path} not found.")
            continue
            
        # Create Image Clip
        img_clip = ImageClip(str(f_path)).with_duration(dur)
        
        # Crop/Resize to 9:16
        orig_w, orig_h = img_clip.size
        scale = max(TARGET_W / orig_w, TARGET_H / orig_h)
        img_clip = img_clip.resized(height=int(orig_h * scale)) if orig_w * scale >= TARGET_W else img_clip.resized(width=int(orig_w * scale))
        
        x_center = img_clip.w / 2
        y_center = img_clip.h / 2
        img_clip = img_clip.cropped(x_center=x_center, y_center=y_center, width=TARGET_W, height=TARGET_H)
        
        clips.append(img_clip)
        
        # Audio mapping
        if i == 0 and "ambient" in sfx:
            total_dur = sum(durations)
            ambient = AudioFileClip(sfx["ambient"]).with_start(0).with_duration(total_dur)
            # Reduce volume
            ambient = ambient.multiply_volume(0.3)
            audio_clips.append(ambient)
            
        if i == 3 and "door_beep" in sfx: # Badge caught
            beep = AudioFileClip(sfx["door_beep"]).with_start(current_time)
            audio_clips.append(beep)
            
        if i == 4 and "shock" in sfx: # Shocked face
            shock = AudioFileClip(sfx["shock"]).with_start(current_time)
            audio_clips.append(shock)
            
        if i == 7 and "train_move" in sfx: # Train leaving
            move = AudioFileClip(sfx["train_move"]).with_start(current_time)
            audio_clips.append(move)
            
        if i == 8 and "boing" in sfx: # Stretched neck
            boing = AudioFileClip(sfx["boing"]).with_start(current_time)
            audio_clips.append(boing)
            
        current_time += dur

    print("Step 3: Stashing everything together...")
    final_video = concatenate_videoclips(clips, method="chain")
    
    if audio_clips:
        final_audio = CompositeAudioClip(audio_clips)
        final_video = final_video.with_audio(final_audio)
    
    output_path = ASSETS_DIR / "subway_commute_final.mp4"
    print(f"Step 4: Rendering to {output_path}...")
    final_video.write_videofile(str(output_path), fps=30, codec="libx264", audio_codec="aac")
    print("\nMission Success! 🚇🐱✨")

if __name__ == "__main__":
    assemble_subway()
