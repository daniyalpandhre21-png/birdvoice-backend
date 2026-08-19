from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

from utils.ebird import get_rarity
from utils.media_fetcher import get_bird_image
from utils.wiki_summary import get_bird_summary

from datetime import datetime
from pathlib import Path
import tempfile
import os
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

import soundfile as sf


app = FastAPI(title="Bird Voice Recognition API")


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# GLOBALS
# =========================================================

analyzer = None

# Only a small number of threads because Render Free has
# limited CPU/RAM.
executor = ThreadPoolExecutor(max_workers=2)


MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_AUDIO_SECONDS = 30


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "status": "BirdVoice API running",
        "service": "FastAPI + BirdNET"
    }


@app.get("/ping")
def ping():
    return {
        "message": "API working"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "birdnet_loaded": analyzer is not None
    }


# =========================================================
# BIRDNET LOADER
# =========================================================

def get_analyzer():

    global analyzer

    if analyzer is None:

        print("===================================")
        print("Loading BirdNET model...")
        print("===================================")

        analyzer = Analyzer()

        print("===================================")
        print("BirdNET model loaded successfully")
        print("===================================")

    return analyzer


# =========================================================
# LOAD BIRDNET IN BACKGROUND THREAD
# =========================================================

def run_birdnet(audio_path, lat, lon):

    model = get_analyzer()

    recording = Recording(
        model,
        audio_path,
        lat=lat,
        lon=lon,
        date=datetime.now(),
        min_conf=0.20
    )

    recording.analyze()

    return recording.detections


# =========================================================
# EXTERNAL INFORMATION
# =========================================================

def get_extra_info(species, scientific_name):

    try:
        rarity = get_rarity(scientific_name)
    except Exception as e:
        print("Rarity error:", e)
        rarity = "unknown"

    try:
        image_url = get_bird_image(
            species,
            scientific_name
        )
    except Exception as e:
        print("Image error:", e)
        image_url = None

    try:
        description = get_bird_summary(species)
    except Exception as e:
        print("Wikipedia error:", e)
        description = ""

    return {
        "rarity": rarity or "unknown",
        "image_url": image_url or
        "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg",
        "description": description or ""
    }


# =========================================================
# IDENTIFY
# =========================================================

@app.post("/identify")
async def identify(
    audio: UploadFile = File(...),
    lat: float = None,
    lon: float = None
):

    tmp_path = None

    try:

        print("===================================")
        print("Request received: /identify")
        print("Filename:", audio.filename)
        print("Content type:", audio.content_type)
        print("===================================")

        # -------------------------------------------------
        # READ FILE
        # -------------------------------------------------

        contents = await audio.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty"
            )

        # -------------------------------------------------
        # FILE SIZE CHECK
        # -------------------------------------------------

        if len(contents) > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=413,
                detail="Audio file is too large. Maximum size is 10 MB."
            )

        # -------------------------------------------------
        # KEEP ORIGINAL EXTENSION
        # -------------------------------------------------

        extension = Path(
            audio.filename or "audio.wav"
        ).suffix.lower()

        if extension not in [".wav", ".mp3", ".ogg", ".flac", ".m4a"]:

            extension = ".wav"

        # -------------------------------------------------
        # SAVE TEMP FILE
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as tmp:

            tmp.write(contents)
            tmp_path = tmp.name

        print("Audio saved:", tmp_path)

        # -------------------------------------------------
        # AUDIO DURATION CHECK
        # -------------------------------------------------

        try:

            info = sf.info(tmp_path)

            duration = info.frames / info.samplerate

            print("Audio duration:", duration)

            if duration > MAX_AUDIO_SECONDS:

                raise HTTPException(
                    status_code=400,
                    detail=f"Audio is too long. Maximum allowed is {MAX_AUDIO_SECONDS} seconds."
                )

        except HTTPException:
            raise

        except Exception as e:

            print("Could not read audio metadata:", e)

        # -------------------------------------------------
        # RUN BIRDNET
        # -------------------------------------------------

        print("Starting BirdNET analysis...")

        loop = asyncio.get_running_loop()

        detections = await loop.run_in_executor(
            executor,
            run_birdnet,
            tmp_path,
            lat or 0,
            lon or 0
        )

        print("BirdNET analysis finished.")

        # -------------------------------------------------
        # NO DETECTION
        # -------------------------------------------------

        if not detections:

            raise HTTPException(
                status_code=404,
                detail="No bird detected in audio"
            )

        # -------------------------------------------------
        # BEST RESULT
        # -------------------------------------------------

        top = max(
            detections,
            key=lambda x: x.get("confidence", 0)
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
            float(top.get("confidence", 0)),
            2
        )

        print("Detected:", species)
        print("Scientific:", scientific_name)
        print("Confidence:", confidence)

        # -------------------------------------------------
        # GET EXTRA INFORMATION
        # -------------------------------------------------

        print("Getting bird information...")

        extra = await loop.run_in_executor(
            executor,
            get_extra_info,
            species,
            scientific_name
        )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        response = {
            "bird": {
                "common_name": species,
                "scientific_name": scientific_name,
                "rarity": extra["rarity"],
                "description": extra["description"]
            },

            "media": {
                "image_url": extra["image_url"],
                "confidence": confidence
            }
        }

        print("Request completed successfully.")

        return response

    # =====================================================
    # HTTP ERRORS
    # =====================================================

    except HTTPException as e:

        raise e

    # =====================================================
    # OTHER ERRORS
    # =====================================================

    except Exception as e:

        print("===================================")
        print("ERROR DURING /identify")
        print("===================================")

        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e)
            }
        )

    # =====================================================
    # DELETE TEMP FILE
    # =====================================================

    finally:

        if tmp_path and os.path.exists(tmp_path):

            try:
                os.remove(tmp_path)
                print("Temporary file deleted.")

            except Exception as e:
                print("Could not delete temporary file:", e)