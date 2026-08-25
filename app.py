import os
# TensorFlow / C++ threading lock to prevent freezes
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
os.environ["TF_NUM_INTEROP_THREADS"] = "1"

import tensorflow as tf
try:
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
except Exception:
    pass

import streamlit as st
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

from utils.ebird import get_rarity
from utils.media_fetcher import get_bird_image
from utils.wiki_summary import get_bird_summary

from datetime import datetime
from pathlib import Path
import tempfile
import soundfile as sf

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="BirdNova | AI Bird Identifier",
    page_icon="🌿",
    layout="wide"
)

# =========================================================
# CUSTOM FOREST & GREENERY CSS THEME (Fixed Text & Readability)
# =========================================================
st.markdown("""
    <style>
    /* Main background & font styling */
    .stApp {
        background-color: #f4f7f4;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1b3022;
        color: #ffffff;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #e2ede5 !important;
    }

    /* Custom Header Style */
    .main-header {
        background: linear-gradient(135deg, #2d5a27 0%, #1b3022 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .main-header p {
        margin-top: 8px;
        font-size: 1.05rem;
        color: #c8e6c9;
    }

    /* Make all standard text dark and readable */
    p, span, label, div {
        color: #2c3e2d;
    }

    /* Instruction Box Styling */
    .instruction-box {
        background-color: #e8f5e9;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 5px solid #2d5a27;
        color: #1b3022;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Result Card Styling */
    .result-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border-left: 6px solid #2d5a27;
        box-shadow: 0 4px 12px rgba(45, 90, 39, 0.08);
        margin-top: 20px;
    }

    /* Custom Button Style */
    .stButton>button {
        background-color: #2d5a27 !important;
        color: white !important;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3b7a33 !important;
        box-shadow: 0 4px 10px rgba(45, 90, 39, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER BANNER
# =========================================================
st.markdown("""
    <div class="main-header">
        <h1>🐦 BirdNova</h1>
        <p>Listen to the canopy. Upload or record a bird call to identify the species using AI & BirdNET.</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# LOAD ANALYZER (CACHED)
# =========================================================
@st.cache_resource
def load_birdnet_analyzer():
    st.info("Loading BirdNET model... Please wait (this happens only once).")
    analyzer = Analyzer()
    return analyzer

try:
    analyzer = load_birdnet_analyzer()
except Exception as e:
    st.error(f"Failed to load BirdNET model: {e}")
    analyzer = None

# =========================================================
# SIDEBAR CONTROLS
# =========================================================
with st.sidebar:
    st.header("🌲 BirdNova Panel")
    st.write("Provide an audio sample via upload or live mic.")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "ogg", "flac", "m4a"]
    )
    
    st.markdown("---")
    st.write("🎙️ **Or Record Live Audio**")
    recorded_audio = st.audio_input("Record bird call")
    
    st.markdown("---")
    st.subheader("📍 Location Details")
    lat = st.number_input("Latitude", value=0.0, format="%.4f")
    lon = st.number_input("Longitude", value=0.0, format="%.4f")
    
    st.markdown("---")
    analyze_btn = st.button("🍃 Identify Bird", type="primary")

active_audio = uploaded_file if uploaded_file is not None else recorded_audio

# =========================================================
# INPUT FORM & EXECUTION
# =========================================================
if analyze_btn:
    if active_audio is None:
        st.warning("⚠️ Please upload an audio file or record a live audio sample first!")
    elif analyzer is None:
        st.error("❌ BirdNET model is not loaded properly.")
    else:
        with st.spinner("🎧 Analyzing audio and identifying bird..."):
            tmp_path = None
            try:
                file_name = getattr(active_audio, "name", "recording.wav")
                extension = Path(file_name).suffix.lower()
                if not extension:
                    extension = ".wav"

                with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                    tmp.write(active_audio.getvalue())
                    tmp_path = tmp.name

                try:
                    info = sf.info(tmp_path)
                    duration = info.frames / info.samplerate
                    if duration > 30:
                        st.error("Audio is too long. Maximum allowed is 30 seconds.")
                        st.stop()
                except Exception:
                    pass

                recording = Recording(
                    analyzer,
                    tmp_path,
                    lat=lat,
                    lon=lon,
                    date=datetime.now(),
                    min_conf=0.10
                )
                recording.analyze()

                detections = recording.detections

                if not detections:
                    st.warning("🌿 No bird detected in the audio. Try a clearer recording or adjust location.")
                else:
                    top = max(detections, key=lambda x: x.get("confidence", 0))
                    species = top.get("common_name", "Unknown bird")
                    scientific_name = top.get("scientific_name", "")
                    confidence = round(float(top.get("confidence", 0)), 2)

                    rarity = "unknown"
                    try:
                        rarity = get_rarity(scientific_name) or "unknown"
                    except Exception:
                        pass

                    image_url = "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg"
                    try:
                        image_url = get_bird_image(species, scientific_name) or image_url
                    except Exception:
                        pass

                    full_description = ""
                    try:
                        full_description = get_bird_summary(species) or ""
                    except Exception:
                        pass

                    # Shorten description to first 2-3 sentences for clean UI
                    if full_description:
                        sentences = full_description.split('. ')
                        short_description = '. '.join(sentences[:3]) + ('.' if not full_description.endswith('.') else '')
                    else:
                        short_description = "No description available for this species."

                    # Display Results inside a clean Forest Card
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.success("🎉 Bird Identified Successfully by BirdNova!")
                    
                    res_col1, res_col2 = st.columns([1, 2])
                    with res_col1:
                        st.image(image_url, caption=species, use_container_width=True)
                    with res_col2:
                        st.subheader(species)
                        st.markdown(f"**Scientific Name:** *{scientific_name}*")
                        st.markdown(f"**Confidence:** `{confidence * 100:.1f}%`")
                        st.markdown(f"**Rarity:** `{rarity}`")

                    st.markdown("### 📖 About the Bird")
                    st.write(short_description)

                    # Optional: Expandable section for full Wikipedia text
                    if full_description and len(full_description) > len(short_description):
                        with st.expander("Read full Wikipedia summary"):
                            st.write(full_description)

                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
else:
    st.markdown("""
        <div class="instruction-box">
            👉 Please upload an audio file or use the live microphone recorder in the sidebar, then click <b>Identify Bird</b> to begin exploring with BirdNova.
        </div>
    """, unsafe_allow_html=True)
