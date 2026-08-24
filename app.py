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
    page_title="Bird Voice Recognition",
    page_icon="🐦",
    layout="centered"
)

st.title("🐦 Bird Voice Recognition System")
st.write("Upload an audio file of a bird's call to identify the species using BirdNET!")

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
# INPUT FORM
# =========================================================
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["wav", "mp3", "ogg", "flac", "m4a"]
)

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude (Optional)", value=0.0, format="%.4f")
with col2:
    lon = st.number_input("Longitude (Optional)", value=0.0, format="%.4f")

if st.button("Identify Bird", type="primary"):
    if uploaded_file is None:
        st.warning("Please upload an audio file first!")
    elif analyzer is None:
        st.error("BirdNET model is not loaded properly.")
    else:
        with st.spinner("Analyzing audio and identifying bird... 🎧"):
            tmp_path = None
            try:
                # Save uploaded file temporarily
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
                    st.warning("No bird detected in the audio. Try another sample or adjust confidence.")
                else:
                    # Get top result
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

                    # Display Results
                    st.success("Bird Identified Successfully! 🎉")
                    
                    res_col1, res_col2 = st.columns([1, 2])
                    with res_col1:
                        st.image(image_url, caption=species, use_container_width=True)
                    with res_col2:
                        st.subheader(species)
                        st.markdown(f"**Scientific Name:** *{scientific_name}*")
                        st.markdown(f"**Confidence:** `{confidence * 100:.1f}%`")
                        st.markdown(f"**Rarity:** `{rarity}`")

                    if description:
                        st.markdown("### About the Bird")
                        st.write(description)

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
