from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
import tempfile, os, traceback
from datetime import datetime
from utils.ebird import get_rarity
from utils.media_fetcher import get_bird_image
from utils.wiki_summary import get_bird_summary

app = FastAPI(title="Bird Voice Recognition API")

# Health check route
@app.get("/")
def home():
    return {"status": "BirdVoice API running"}

# Lazy load BirdNET model
analyzer = None

def get_analyzer():
    global analyzer
    if analyzer is None:
        print("Loading BirdNET model...")
        analyzer = Analyzer()
        print("BirdNET model loaded.")
    return analyzer

# CORS allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/identify")
async def identify(audio: UploadFile = File(...), lat: float = None, lon: float = None):
    tmp_path = None
    try:
        contents = await audio.read()

        if not contents:
            return JSONResponse(
                content={"error": "Uploaded file is empty"},
                status_code=400
            )

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        date_obj = datetime.now()

        recording = Recording(
            get_analyzer(),
            tmp_path,
            lat=lat or 0,
            lon=lon or 0,
            date=date_obj,
            min_conf=0.1,
        )

        print("Analyzing audio...")
        recording.analyze()

        if not recording.detections:
            raise HTTPException(status_code=404, detail="No bird detected in audio")

        # Get top detection
        top = sorted(
            recording.detections,
            key=lambda x: x["confidence"],
            reverse=True
        )[0]

        species = top["common_name"]
        scientific_name = top["scientific_name"]
        confidence = round(top["confidence"], 2)

        rarity = get_rarity(scientific_name) or "unknown"
        image_url = get_bird_image(
            species,
            scientific_name
        ) or "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg"

        description = get_bird_summary(species) or ""

        return {
            "bird": {
                "common_name": species,
                "scientific_name": scientific_name,
                "rarity": rarity,
                "description": description
            },
            "media": {
                "image_url": image_url,
                "confidence": confidence
            }
        }

    except Exception as e:
        print("ERROR during /identify request:")
        traceback.print_exc()

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)