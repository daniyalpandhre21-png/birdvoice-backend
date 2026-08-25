import os

# =========================================================
# THREADING SETTINGS
# =========================================================

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


# =========================================================
# IMPORTS
# =========================================================

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
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="BirdNova | AI Bird Identifier",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

/* =====================================================
   GLOBAL
===================================================== */

.stApp {
    background: #f5f8f5;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* =====================================================
   HERO
===================================================== */

.hero {
    background: linear-gradient(
        135deg,
        #173d25 0%,
        #245c32 50%,
        #367a43 100%
    );

    padding: 42px 35px;
    border-radius: 24px;
    text-align: center;
    margin-bottom: 28px;

    box-shadow: 0 10px 30px rgba(25, 70, 35, 0.15);
}

.hero-icon {
    font-size: 54px;
    margin-bottom: 5px;
}

.hero-title {
    color: white !important;
    font-size: 42px;
    font-weight: 800;
    margin: 0;
    letter-spacing: 1px;
}

.hero-subtitle {
    color: #d9f0dd !important;
    font-size: 17px;
    margin-top: 10px;
}


/* =====================================================
   SECTION TITLES
===================================================== */

.section-title {
    color: #173d25 !important;
    font-size: 23px;
    font-weight: 750;
    margin-top: 10px;
    margin-bottom: 15px;
}


/* =====================================================
   FEATURE CARDS
===================================================== */

.feature-card {
    background: white;
    padding: 23px;
    border-radius: 18px;
    text-align: center;
    min-height: 150px;

    border: 1px solid #e0ebe2;

    box-shadow: 0 5px 18px rgba(35, 80, 45, 0.07);
}

.feature-icon {
    font-size: 34px;
}

.feature-title {
    color: #173d25 !important;
    font-size: 18px;
    font-weight: 700;
    margin-top: 8px;
}

.feature-text {
    color: #607264 !important;
    font-size: 14px;
}


/* =====================================================
   INPUT CARD
===================================================== */

.input-card {
    background: white;
    padding: 25px;
    border-radius: 20px;

    border: 1px solid #e0ebe2;

    box-shadow: 0 5px 18px rgba(35, 80, 45, 0.07);

    margin-top: 28px;
    margin-bottom: 20px;
}


/* =====================================================
   SIDEBAR
===================================================== */

[data-testid="stSidebar"] {
    background: #173d25;
    display: block !important;
    visibility: visible !important;
}

[data-testid="stSidebar"] * {
    color: #eef7f0 !important;
}

.sidebar-brand {
    text-align: center;
    padding: 10px 0 20px 0;
}

.sidebar-brand-icon {
    font-size: 42px;
}

.sidebar-brand-title {
    color: white !important;
    font-size: 25px;
    font-weight: 800;
}

.sidebar-brand-text {
    color: #cde3d1 !important;
    font-size: 13px;
}


/* =====================================================
   BUTTON
===================================================== */

.stButton > button {
    width: 100%;

    background: linear-gradient(
        135deg,
        #2f743d,
        #1f5a2d
    ) !important;

    color: white !important;

    border: none !important;
    border-radius: 12px !important;

    padding: 13px 20px !important;

    font-size: 16px !important;
    font-weight: 700 !important;

    box-shadow: 0 5px 15px rgba(35, 100, 50, 0.22);

    transition: 0.2s;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(35, 100, 50, 0.28);
}


/* =====================================================
   RESULT CARD
===================================================== */

.result-card {
    background: white;

    padding: 30px;

    border-radius: 22px;

    border: 1px solid #dce9de;

    box-shadow: 0 8px 28px rgba(35, 80, 45, 0.10);

    margin-top: 25px;
}

.result-header {
    color: #1d6130 !important;
    font-size: 19px;
    font-weight: 750;
    margin-bottom: 20px;
}

.bird-name {
    color: #173d25 !important;
    font-size: 31px;
    font-weight: 800;
    margin-bottom: 3px;
}

.scientific-name {
    color: #708174 !important;
    font-size: 16px;
    font-style: italic;
    margin-bottom: 20px;
}


/* =====================================================
   INFO BOXES
===================================================== */

.info-box {
    background: #f1f7f2;
    border-radius: 13px;
    padding: 14px;
    text-align: center;
    border: 1px solid #dfece1;
}

.info-label {
    color: #718073 !important;
    font-size: 12px;
    font-weight: 600;
}

.info-value {
    color: #1d6130 !important;
    font-size: 18px;
    font-weight: 750;
    margin-top: 3px;
}


/* =====================================================
   ABOUT
===================================================== */

.about-box {
    background: #f6faf6;
    border-left: 5px solid #367a43;

    padding: 20px;

    border-radius: 10px;

    color: #354a39 !important;

    line-height: 1.7;

    margin-top: 20px;
}


/* =====================================================
   FOOTER
===================================================== */

.footer {
    text-align: center;

    color: #829084 !important;

    font-size: 13px;

    margin-top: 50px;

    padding-top: 20px;

    border-top: 1px solid #dce7de;
}


/* =====================================================
   STREAMLIT BRANDING
===================================================== */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}


/* =====================================================
   MOBILE
===================================================== */

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding: 30px 20px;
        border-radius: 20px;
    }

    .hero-icon {
        font-size: 45px;
    }

    .hero-title {
        font-size: 34px;
    }

    .hero-subtitle {
        font-size: 15px;
    }

    .feature-card {
        margin-bottom: 12px;
    }

    .bird-name {
        font-size: 26px;
    }

}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">
<div class="hero-icon">🐦</div>
<div class="hero-title">BirdNova</div>
<div class="hero-subtitle">AI-powered bird sound identification</div>
<div class="hero-subtitle">Upload a recording or use your microphone to discover the bird.</div>
</div>
""",
    unsafe_allow_html=True
)


# =========================================================
# FEATURE CARDS
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.markdown(
        """
<div class="feature-card">
<div class="feature-icon">🎙️</div>
<div class="feature-title">Record</div>
<div class="feature-text">
Capture a bird call using your microphone.
</div>
</div>
""",
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
<div class="feature-card">
<div class="feature-icon">🧠</div>
<div class="feature-title">AI Detection</div>
<div class="feature-text">
BirdNET analyzes the sound and identifies the species.
</div>
</div>
""",
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        """
<div class="feature-card">
<div class="feature-icon">🌿</div>
<div class="feature-title">Discover</div>
<div class="feature-text">
Explore species information, rarity and images.
</div>
</div>
""",
        unsafe_allow_html=True
    )


st.write("")


# =========================================================
# LOAD BIRDNET ANALYZER
# =========================================================

@st.cache_resource
def load_birdnet_analyzer():

    analyzer = Analyzer()

    return analyzer


try:

    with st.spinner("🧠 Loading BirdNET AI model..."):

        analyzer = load_birdnet_analyzer()

except Exception as e:

    analyzer = None

    st.error(
        f"BirdNET model could not be loaded: {e}"
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
<div class="sidebar-brand">
<div class="sidebar-brand-icon">🐦</div>
<div class="sidebar-brand-title">BirdNova</div>
<div class="sidebar-brand-text">AI Bird Identification</div>
</div>
""",
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.subheader("🎵 Audio")

    uploaded_file = st.file_uploader(
        "Upload bird audio",
        type=[
            "wav",
            "mp3",
            "ogg",
            "flac",
            "m4a"
        ]
    )

    st.write("or")

    recorded_audio = st.audio_input(
        "🎙️ Record bird call"
    )

    st.markdown("---")

    st.subheader("📍 Location")

    lat = st.number_input(
        "Latitude",
        value=0.0,
        format="%.4f"
    )

    lon = st.number_input(
        "Longitude",
        value=0.0,
        format="%.4f"
    )

    st.markdown("---")

    analyze_btn = st.button(
        "🐦 Identify Bird"
    )


# =========================================================
# ACTIVE AUDIO
# =========================================================

active_audio = (
    uploaded_file
    if uploaded_file is not None
    else recorded_audio
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze_btn:

    if active_audio is None:

        st.warning(
            "🎙️ Please upload an audio file or record a bird call first."
        )

    elif analyzer is None:

        st.error(
            "❌ BirdNET model is not available."
        )

    else:

        with st.spinner(
            "🎧 Listening to the recording and identifying the bird..."
        ):

            tmp_path = None

            try:

                # =================================================
                # FILE INFORMATION
                # =================================================

                file_name = getattr(
                    active_audio,
                    "name",
                    "recording.wav"
                )

                extension = Path(
                    file_name
                ).suffix.lower()

                if not extension:

                    extension = ".wav"


                # =================================================
                # TEMPORARY AUDIO FILE
                # =================================================

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=extension
                ) as tmp:

                    tmp.write(
                        active_audio.getvalue()
                    )

                    tmp_path = tmp.name


                # =================================================
                # AUDIO DURATION
                # =================================================

                try:

                    info = sf.info(tmp_path)

                    duration = (
                        info.frames /
                        info.samplerate
                    )

                    if duration > 30:

                        st.error(
                            "⏱️ Audio is too long. "
                            "Maximum allowed duration is 30 seconds."
                        )

                        st.stop()

                except Exception:

                    pass


                # =================================================
                # CREATE BIRDNET RECORDING
                # =================================================

                recording = Recording(
                    analyzer,
                    tmp_path,
                    lat=lat,
                    lon=lon,
                    date=datetime.now(),
                    min_conf=0.10
                )


                # =================================================
                # ANALYZE AUDIO
                # =================================================

                recording.analyze()


                # =================================================
                # GET DETECTIONS
                # =================================================

                detections = recording.detections


                # =================================================
                # NO DETECTION
                # =================================================

                if not detections:

                    st.warning(
                        "🌿 No bird was detected in this recording."
                    )

                    st.info(
                        "Try a clearer recording with less background noise."
                    )


                else:

                    # =================================================
                    # BEST DETECTION
                    # =================================================

                    top = max(
                        detections,
                        key=lambda x: x.get(
                            "confidence",
                            0
                        )
                    )


                    species = top.get(
                        "common_name",
                        "Unknown bird"
                    )

                    scientific_name = top.get(
                        "scientific_name",
                        ""
                    )

                    confidence = round(
                        float(
                            top.get(
                                "confidence",
                                0
                            )
                        ),
                        2
                    )


                    # =================================================
                    # RARITY
                    # =================================================

                    rarity = "unknown"

                    try:

                        rarity = (
                            get_rarity(
                                scientific_name
                            )
                            or "unknown"
                        )

                    except Exception:

                        pass


                    # =================================================
                    # IMAGE
                    # =================================================

                    image_url = (
                        "https://upload.wikimedia.org/"
                        "wikipedia/commons/6/65/"
                        "No-Image-Placeholder.svg"
                    )

                    try:

                        image_url = (
                            get_bird_image(
                                species,
                                scientific_name
                            )
                            or image_url
                        )

                    except Exception:

                        pass


                    # =================================================
                    # WIKIPEDIA DESCRIPTION
                    # =================================================

                    full_description = ""

                    try:

                        full_description = (
                            get_bird_summary(
                                species
                            )
                            or ""
                        )

                    except Exception:

                        pass


                    # =================================================
                    # SHORT DESCRIPTION
                    # =================================================

                    if full_description:

                        sentences = (
                            full_description.split(". ")
                        )

                        short_description = (
                            ". ".join(
                                sentences[:3]
                            )
                        )

                        if (
                            short_description
                            and
                            not short_description.endswith(".")
                        ):

                            short_description += "."

                    else:

                        short_description = (
                            "No description available "
                            "for this species."
                        )


                    # =================================================
                    # RESULT CARD
                    # =================================================

                    st.markdown(
                        '<div class="result-card">',
                        unsafe_allow_html=True
                    )


                    st.markdown(
                        """
<div class="result-header">
🎉 Bird Identified Successfully
</div>
""",
                        unsafe_allow_html=True
                    )


                    result_col1, result_col2 = st.columns(
                        [1, 1.5],
                        gap="large"
                    )


                    # =================================================
                    # BIRD IMAGE
                    # =================================================

                    with result_col1:

                        st.image(
                            image_url,
                            caption=species,
                            use_container_width=True
                        )


                    # =================================================
                    # BIRD INFORMATION
                    # =================================================

                    with result_col2:

                        st.markdown(
                            f"""
<div class="bird-name">
{species}
</div>

<div class="scientific-name">
{scientific_name}
</div>
""",
                            unsafe_allow_html=True
                        )


                        info1, info2 = st.columns(2)


                        with info1:

                            st.markdown(
                                f"""
<div class="info-box">
<div class="info-label">CONFIDENCE</div>
<div class="info-value">
{confidence * 100:.1f}%
</div>
</div>
""",
                                unsafe_allow_html=True
                            )


                        with info2:

                            st.markdown(
                                f"""
<div class="info-box">
<div class="info-label">RARITY</div>
<div class="info-value">
{rarity.title()}
</div>
</div>
""",
                                unsafe_allow_html=True
                            )


                        st.write("")


                        st.markdown(
                            "#### 🎯 Detection Confidence"
                        )


                        st.progress(
                            min(
                                max(
                                    confidence,
                                    0.0
                                ),
                                1.0
                            )
                        )


                    # =================================================
                    # ABOUT BIRD
                    # =================================================

                    st.markdown(
                        """
<div class="section-title">
📖 About this Bird
</div>
""",
                        unsafe_allow_html=True
                    )


                    st.markdown(
                        f"""
<div class="about-box">
{short_description}
</div>
""",
                        unsafe_allow_html=True
                    )


                    # =================================================
                    # FULL DESCRIPTION
                    # =================================================

                    if (
                        full_description
                        and
                        len(full_description)
                        > len(short_description)
                    ):

                        with st.expander(
                            "📚 Read full species information"
                        ):

                            st.write(
                                full_description
                            )


                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True
                    )


            # =====================================================
            # ERROR HANDLING
            # =====================================================

            except Exception as e:

                st.error(
                    f"❌ An error occurred during analysis: {e}"
                )


            # =====================================================
            # CLEAN TEMP FILE
            # =====================================================

            finally:

                if (
                    tmp_path
                    and
                    os.path.exists(tmp_path)
                ):

                    try:

                        os.remove(tmp_path)

                    except Exception:

                        pass


else:

    # =========================================================
    # EMPTY STATE
    # =========================================================

    st.markdown(
        """
<div class="input-card">

<div class="section-title">
🌿 Start Your Bird Discovery
</div>

<p style="color:#607264;font-size:16px;line-height:1.7;">
Upload a bird recording from the sidebar or record one using your microphone.
</p>

<p style="color:#607264;font-size:16px;line-height:1.7;">
BirdNova will analyze the sound using BirdNET and show the most likely species, confidence, rarity and additional information.
</p>

</div>
""",
        unsafe_allow_html=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
<div class="footer">
🐦 <b>BirdNova</b> · AI Bird Sound Recognition
<br><br>
Powered by BirdNET · Built with Python & Streamlit
</div>
""",
    unsafe_allow_html=True
)
