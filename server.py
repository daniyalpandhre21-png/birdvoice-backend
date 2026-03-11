from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from pydub import AudioSegment
import tempfile, os, traceback
from datetime import datetime

from utils.ebird import get_rarity
from utils.media_fetcher import get_bird_image
from utils.wiki_summary import get_bird_summary

app = FastAPI(title="Bird Voice Recognition API")

@app.get("/")
def home():
    return {"status": "BirdVoice API running"}

# analyzer lazy load
analyzer = None

def get_analyzer():
    global analyzer
    if analyzer is None:
        print("STEP 0: Loading BirdNET model...")
        analyzer = Analyzer()
        print("STEP 0: BirdNET model loaded")
    return analyzer

# allow requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/identify")
async def identify(audio: UploadFile = File(...), lat: float = None, lon: float = None):

    tmp_path = None

    try:
        print("STEP 1: request received")

        contents = await audio.read()
        print("STEP 2: audio read")

        if not contents:
            raise HTTPException(status_code=400, detail="Empty audio file")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        print("STEP 3: audio saved:", tmp_path)

        # load audio
        sound = AudioSegment.from_file(tmp_path)
        print("STEP 4: audio loaded")

        # trim to 8 seconds
        sound = sound[:8000]
        sound.export(tmp_path, format="wav")

        print("STEP 5: audio trimmed")

        analyzer = get_analyzer()
        print("STEP 6: analyzer ready")

        recording = Recording(
            analyzer,
            tmp_path,
            lat=lat or 0,
            lon=lon or 0,
            date=datetime.now(),
            min_conf=0.1,
        )

        print("STEP 7: recording object created")

        print("STEP 8: starting analysis")
        recording.analyze()

        print("STEP 9: analysis finished")

        if not recording.detections:
            raise HTTPException(status_code=404, detail="No bird detected")

        top = sorted(
            recording.detections,
            key=lambda x: x["confidence"],
            reverse=True
        )[0]

        species = top["common_name"]
        scientific_name = top["scientific_name"]
        confidence = round(top["confidence"], 2)

        print("STEP 10: bird detected:", species)

        rarity = get_rarity(scientific_name) or "unknown"
        image_url = get_bird_image(species, scientific_name)
        description = get_bird_summary(species)

        return {
            "bird": {
                "common_name": species,
                "scientific_name": scientific_name,
                "rarity": rarity,
                "description": description or ""
            },
            "media": {
                "image_url": image_url,
                "confidence": confidence
            }
        }

    except Exception as e:
        print("ERROR during identify")
        traceback.print_exc()

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print("STEP 11: temp file removed")