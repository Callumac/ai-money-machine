import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import (
    TextClip, concatenate_videoclips, AudioFileClip,
    CompositeVideoClip, VideoFileClip, afx
)
import qrcode
import zipfile
import uuid
import logging
import time
import numpy as np
from datetime import datetime

# ─── 0. AUTHENTICATION ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Money Machine",
    page_icon="💸",
    layout="centered",
    initial_sidebar_state="auto"
)
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Password from ENV
APP_PASSWORD = os.getenv("APP_PASSWORD")
password = st.sidebar.text_input("🔒 Enter password", type="password")
if password != APP_PASSWORD:
    st.sidebar.error("Invalid password")
    st.stop()

# ─── 1. GOOGLE ADSENSE ─────────────────────────────────────────────
ADSENSE_ID = os.getenv("ADSENSE_ID")
adsense_snippet = f"""
<!-- Google AdSense -->
<script data-ad-client=\"{ADSENSE_ID}\" async
  src=\"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js\"></script>
"""
components.html(adsense_snippet, height=0)

# ─── 2. PREPARE DIRECTORIES ─────────────────────────────────────────
OUTPUT = "output"
ASSETS = "assets"
os.makedirs(OUTPUT, exist_ok=True)
# Ensure assets contains: abstract.mp4, nature.mp4, tech.mp4

# ─── 3. SIDEBAR METRICS & INSTRUCTIONS ─────────────────────────────
st.sidebar.title("Usage & Instructions")
if "count" not in st.session_state:
    st.session_state.count = 0
st.sidebar.write(f"Packages generated: {st.session_state.count}")
st.sidebar.markdown(
    """
**Steps:**
1. Enter Niche, Tone, and Landing Page URL
2. (Optional) Upload BGM and choose background
3. Click Generate
4. Download ZIP and post!
"""
)

# ─── 4. INPUT FORM ─────────────────────────────────────────────────
with st.form("gen_form", clear_on_submit=False):
    niche = st.text_input(
        "Niche (e.g. accident analysis)",
        placeholder="Generate viral accident video"
    )
    tone = st.selectbox(
        "Tone / Style",
        ["Motivational", "Tips & Tricks", "Controversial", "Review", "How-to"]
    )
    url = st.text_input(
        "Landing Page / CPA URL",
        placeholder="https://your.link/offer"
    )
    include_bgm = st.checkbox("Include background music (optional)", value=False)
    bgm_file = None
    if include_bgm:
        bgm_file = st.file_uploader("Upload BGM (MP3)", type=["mp3"])
    bg_choice = st.selectbox(
        "Video background",
        ["Plain black", "Abstract loop", "Nature loop", "Tech loop"]
    )
    generate = st.form_submit_button("Generate Video Package")

# ─── 5. GENERATION WORKFLOW ─────────────────────────────────────────
if generate:
    if not (niche and tone and url):
        st.error("Please fill in all fields.")
    else:
        st.session_state.count += 1
        start_time = time.time()
        uid = uuid.uuid4().hex[:8]
        logger.info(f"START uid={uid} niche={niche} tone={tone}")

        # 5.1 SCRIPT
        script = (
            f"{niche}\n"
            f"This {tone.lower()} hack is viral—check: {url}\n"
            f"#{niche.replace(' ', '').lower()} #viral #moneymaker"
        )
        script_path = f"{OUTPUT}/script_{uid}.txt"
        with open(script_path, "w") as f:
            f.write(script)
        st.text_area("📝 Script", script, height=150)

        # 5.2 AUDIO
        with st.spinner("Generating audio…"):
            audio_path = f"{OUTPUT}/audio_{uid}.mp3"
            gTTS(script).save(audio_path)
            audio_clip = AudioFileClip(audio_path).audio_fadein(1).audio_fadeout(1)
            audio_clip.write_audiofile(audio_path, verbose=False, logger=None)
        st.success("Audio ready")

        # 5.3 QR CODE
        qr_path = f"{OUTPUT}/qr_{uid}.png"
        qrcode.make(url).save(qr_path)

        # 5.4 BACKGROUND VIDEO
        bg_path = None
        if bg_choice != "Plain black":
            bg_map = {
                "Abstract loop": f"{ASSETS}/abstract.mp4",
                "Nature loop": f"{ASSETS}/nature.mp4",
                "Tech loop": f"{ASSETS}/tech.mp4"
            }
            bg_path = bg_map.get(bg_choice)

        # 5.5 VIDEO CREATION
        with st.spinner("Building video…"):
            lines = script.split("\n")
            clips = []
            for line in lines:
                txt = (TextClip(
                    line, fontsize=48, color="white",
                    size=(720, 1280), method="caption"
                ).set_duration(3).set_position("center").crossfadein(0.5))
                clips.append(txt)

            video = concatenate_videoclips(clips, method="compose")
            if bg_path and os.path.exists(bg_path):
                bg_clip = VideoFileClip(bg_path).loop(duration=video.duration)
                video = CompositeVideoClip([bg_clip, video])

            video = video.set_audio(audio_clip)

            # Overlay QR
            qr_img = Image.open(qr_path).resize((150, 150)).convert("RGBA")
            qr_arr = np.array(qr_img)
            qr_clip = (ImageClip(qr_arr)
                       .set_duration(video.duration)
                       .set_position(("right", "bottom")))
            video = CompositeVideoClip([video, qr_clip])

            video_path = f"{OUTPUT}/video_{uid}.mp4"
            video.write_videofile(
                video_path, fps=24, codec="libx264",
                audio_codec="aac", verbose=False, logger=None
            )
        st.video(video_path)
        st.success("Video ready")

        # 5.6 THUMBNAIL
        with st.spinner("Creating thumbnail…"):
            thumb_path = f"{OUTPUT}/thumbnail_{uid}.jpg"
            img = Image.new("RGB", (720, 1280), color=(20, 20, 20))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
            )
            draw.text((40, 600), niche, font=font, fill="yellow")
            qr_thumb = Image.open(qr_path).resize((150, 150))
            img.paste(qr_thumb, (560, 1100))
            img.save(thumb_path)
        st.image(thumb_path, caption="Thumbnail")
        st.success("Thumbnail ready")

        # 5.7 ZIP & DOWNLOAD
        zip_path = f"{OUTPUT}/package_{uid}.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            for file in [script_path, audio_path, video_path, thumb_path]:
                z.write(file, os.path.basename(file))
        with open(zip_path, "rb") as zf:
            st.download_button(
                "Download ZIP Package",
                zf,
                file_name="content_package.zip"
            )

        elapsed = time.time() - start_time
        logger.info(f"END uid={uid} elapsed={elapsed:.1f}s")
        st.success(f"Done in {elapsed:.1f}s!")

