# File: app.py
import os
import streamlit as st
import uuid
import time
import logging
import zipfile
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import qrcode
from moviepy.editor import *
import webvtt

# ==============================================================================
#                             CONFIGURATION SETTINGS
# ==============================================================================
class Config:
    # Security & Authentication
    APP_PASSWORD = os.getenv("APP_PASSWORD", "default_password")
    ADSENSE_ID = os.getenv("ADSENSE_ID", "")
    
    # Video Settings
    VIDEO_SIZE = (720, 1280)
    FONT_PATH = "assets/fonts/DejaVuSans-Bold.ttf"
    BG_PATHS = {
        "Abstract": "assets/backgrounds/abstract.mp4",
        "Nature": "assets/backgrounds/nature.mp4",
        "Tech": "assets/backgrounds/tech.mp4"
    }
    
    # SEO & Content
    HASHTAGS = {
        "general": ["#Viral2024", "#MoneyHack", "#SuccessTips"],
        "marketing": ["#DigitalMarketing", "#SEO", "#GrowthHacking"],
        "finance": ["#Investing", "#FinancialFreedom", "#WealthBuilding"]
    }

# ==============================================================================
#                               CORE FUNCTIONS
# ==============================================================================
def generate_seo_content(niche: str, url: str) -> dict:
    """Generate SEO-optimized metadata and hashtags"""
    return {
        "title": f"{niche} Secret Revealed 2024",
        "description": f"Discover the viral {niche} method. Click here: {url}",
        "hashtags": Config.HASHTAGS.get(niche.lower(), Config.HASHTAGS["general"])[:3],
        "keywords": [niche, "make money online", "viral method"]
    }

def create_video_thumbnail(title: str, hashtags: list, qr_path: str) -> Image:
    """Generate YouTube-style thumbnail with text and QR code"""
    img = Image.new("RGB", (1280, 720), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    # Title Text
    font = ImageFont.truetype(Config.FONT_PATH, 60)
    draw.text((100, 100), title, fill="#FFD700", font=font)
    
    # Hashtags
    font_small = ImageFont.truetype(Config.FONT_PATH, 35)
    draw.text((100, 600), " ".join(hashtags), fill="white", font=font_small)
    
    # QR Code
    qr_img = Image.open(qr_path).resize((200, 200))
    img.paste(qr_img, (1000, 500))
    
    return img

def generate_captions(script: str, duration: float) -> str:
    """Create WebVTT captions file with timed text"""
    captions = webvtt.WebVTT()
    lines = script.split("\n")
    segment = duration / len(lines)
    
    for i, line in enumerate(lines):
        start = i * segment
        end = (i + 1) * segment
        captions.captions.append(
            webvtt.Caption(
                f"{start:.3f} --> {end:.3f}",
                line
            )
        )
    return captions

# ==============================================================================
#                               STREAMLIT APP
# ==============================================================================
def main():
    # App Configuration
    st.set_page_config(page_title="AI Money Machine", page_icon="💸", layout="centered")
    
    # Authentication
    if not authenticate_user():
        return
    
    # Main UI
    st.title("AI Money Machine Generator 💰")
    with st.form("generator_form"):
        niche = st.text_input("Enter Niche (e.g. Online Marketing)", placeholder="Digital Marketing Secrets")
        url = st.text_input("Affiliate URL", placeholder="https://your-offer-link.com")
        bg_choice = st.selectbox("Video Background", list(Config.BG_PATHS.keys()))
        
        if st.form_submit_button("🚀 Generate Content Package"):
            process_generation(niche, url, bg_choice)

def authenticate_user() -> bool:
    """Handle password authentication"""
    password = st.sidebar.text_input("🔒 Enter Password", type="password")
    if password != Config.APP_PASSWORD:
        st.sidebar.error("Incorrect Password")
        return False
    return True

def process_generation(niche: str, url: str, bg_choice: str):
    """Main content generation workflow"""
    uid = uuid.uuid4().hex[:8]
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            # Generate SEO Content
            seo = generate_seo_content(niche, url)
            
            # Create Script
            script = f"{seo['title']}\n\n{seo['description']}\n\n{' '.join(seo['hashtags'])}"
            
            # Generate Audio
            tts = gTTS(script)
            audio_path = os.path.join(tmp_dir, f"audio_{uid}.mp3")
            tts.save(audio_path)
            
            # Generate QR Code
            qr_path = os.path.join(tmp_dir, f"qr_{uid}.png")
            qrcode.make(url).save(qr_path)
            
            # Create Video
            video_path = render_video(script, audio_path, bg_choice, uid, tmp_dir)
            
            # Generate Thumbnail
            thumbnail = create_video_thumbnail(seo["title"], seo["hashtags"], qr_path)
            thumb_path = os.path.join(tmp_dir, f"thumb_{uid}.jpg")
            thumbnail.save(thumb_path)
            
            # Create Captions
            captions = generate_captions(script, VideoFileClip(video_path).duration)
            captions_path = os.path.join(tmp_dir, f"captions_{uid}.vtt")
            captions.save(captions_path)
            
            # Create ZIP Package
            zip_path = create_zip_package(tmp_dir, uid, [video_path, audio_path, thumb_path, captions_path])
            
            # Display Results
            show_results(zip_path, video_path, thumb_path, start_time)
            
        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            logging.exception("Generation Error")

def render_video(script: str, audio_path: str, bg_choice: str, uid: str, tmp_dir: str) -> str:
    """Generate video with captions and background"""
    # Create text clips
    clips = [
        TextClip(
            line,
            fontsize=45,
            color="white",
            font=Config.FONT_PATH,
            size=Config.VIDEO_SIZE,
            method="caption"
        ).set_duration(3)
        for line in script.split("\n")
    ]
    
    # Combine clips
    video = concatenate_videoclips(clips, method="compose")
    
    # Add background
    if bg_choice in Config.BG_PATHS and os.path.exists(Config.BG_PATHS[bg_choice]):
        bg_clip = VideoFileClip(Config.BG_PATHS[bg_choice]).loop(duration=video.duration)
        video = CompositeVideoClip([bg_clip, video])
    
    # Add audio
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)
    
    # Save video
    video_path = os.path.join(tmp_dir, f"video_{uid}.mp4")
    video.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="ultrafast"
    )
    return video_path

def create_zip_package(tmp_dir: str, uid: str, files: list) -> str:
    """Package all assets into ZIP file"""
    zip_path = os.path.join(tmp_dir, f"package_{uid}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))
    return zip_path

def show_results(zip_path: str, video_path: str, thumb_path: str, start_time: float):
    """Display generated content and download button"""
    st.video(video_path)
    st.image(Image.open(thumb_path), caption="Generated Thumbnail")
    
    with open(zip_path, "rb") as f:
        st.download_button(
            "📦 Download Content Package",
            f,
            file_name="content_package.zip",
            mime="application/zip"
        )
    
    st.success(f"✅ Generation completed in {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    main()
