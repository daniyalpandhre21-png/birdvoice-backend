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
# PAGE CONFIGURATION (Wide Mode)
# =========================================================
st.set_page_config(
    page_title="BirdNova | AI Bird Identifier",
    page_icon="🌿",
    layout="wide"
)

# =========================================================
# CUSTOM FOREST & GREENERY CSS THEME
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
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .main-header p {
        margin-top: 10px;
        font-size: 1.1rem;
        color: #c8e6c9;
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
        <p>Listen to the canopy. Upload a bird call to identify the species using AI & BirdNET.</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# LOAD ANALYZER (CACHED)
# =========================================================
@st.cache_resource
def load_birdnet_analyzer():
    return Analyzer()

try:
    analyzer = load_birdnet_analyzer()
except Exception as e:
    st.error(f"Failed to load BirdNET model: {e}")
    analyzer = None

# =========================================================
# SIDEBAR CONTROLS (Greenery Theme Input Panel)
# =========================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=70)
    st.header("🌲 BirdNova Control Panel")
    st.write("Configure your audio sample and location parameters.")
    
    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["wav", "mp3", "ogg", "flac", "m4a"]
    )
    
    st.markdown("---")
    st.subheader("📍 Location Details")
    lat = st.number_input("Latitude", value=0.0, format="%.4f")
    lon = st.number_input("Longitude", value=0.0, format="%.4f")
    
    st.markdown("---")
    analyze_btn = st.button("🍃 Identify Bird", type="primary")

# =========================================================
# MAIN CONTENT & ANALYSIS LOGIC
# =========================================================
if analyze_btn:
    if uploaded_file is None:
        st.warning("⚠️ Please upload an audio file from the sidebar first!")
    elif analyzer is None:
        st.error("❌ BirdNET model is not loaded properly.")
    else:
        with st.spinner("🎧 BirdNova is walking through the audio... analyzing calls..."):
            tmp_path = None
            try:
                extension = Path(uploaded_file.name).suffix.lower()
                if not extension:
                    extension = ".wav"

                with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                # Check duration
                try:
                    info = sf.info(tmp_path)
                    duration = info.frames / info.samplerate
                    if duration > 30:
                        st.error("Audio is too long. Maximum allowed is 30 seconds.")
                        st.stop()
                except Exception:
                    pass

                # Run BirdNET Recording Analysis
                recording = Recording(
                    analyzer,
                    tmp_path,
                    lat=lat,
                    lon=lon,
                    date=datetime.now(),
                    min_conf=0.20
                )
                recording.analyze()
                detections = recording.detections

                if not detections:
                    st.warning("🌿 No bird detected in this audio. Try a clearer recording.")
                else:
                    top = max(detections, key=lambda x: x.get("confidence", 0))
                    species = top.get("common_name", "Unknown bird")
                    scientific_name = top.get("scientific_name", "")
                    confidence = round(float(top.get("confidence", 0)), 2)

                    # Fetch Extra Info
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

                    description = ""
                    try:
                        description = get_bird_summary(species) or ""
                    except Exception:
                        pass

                    # Display Results inside a clean Forest Card
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.success("🎉 Bird Identified Successfully by BirdNova!")
                    
                    res_col1, res_col2 = st.columns([1, 2])
                    with res_col1:
                        st.image(image_url, caption=species, use_container_width=True)
                    with res_col2:
                        st.subheader(species)
                        st.markdown(f"**Scientific Name:** *{scientific_name}*")
                        st.markdown(f"**Confidence Score:** `{confidence * 100:.1f}%`")
                        st.markdown(f"**Species Rarity:** `{rarity}`")

                    if description:
                        st.markdown("### 📖 About this Bird")
                        st.write(description)
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
    st.info("👈 Please use the sidebar controls to upload an audio file and click **Identify Bird** to start exploring with BirdNova.")
