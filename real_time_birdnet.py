# real_time_birdnet.py
import sounddevice as sd
import soundfile as sf
import tempfile
import os
from datetime import datetime
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from utils.media_fetcher import get_bird_image
from utils.ebird import get_rarity

analyzer = Analyzer()

def record_audio(duration=5, fs=44100):
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    print("Recording complete!")

    if audio_data is None or len(audio_data) == 0:
        print("Error: No audio captured")
        return None
    return audio_data, fs

def analyze_audio(audio_data, fs, lat=0, lon=0):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            sf.write(tmp, audio_data, fs)
            tmp_path = tmp.name

        date_obj = datetime.now()

        recording = Recording(
            analyzer,
            tmp_path,
            lat=lat,
            lon=lon,
            date=date_obj,
            min_conf=0.1
        )
        recording.analyze()

        if not recording.detections:
            print("No bird detected in audio")
            return []

        detections = sorted(recording.detections, key=lambda x: x["confidence"], reverse=True)

        # Add image and rarity info
        for det in detections:
            det["rarity"] = get_rarity(det["scientific_name"], lat, lon) or "unknown"
            det["image_url"] = get_bird_image(det["common_name"]) or "https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg"

        return detections

    except Exception as e:
        print("Error during analysis:")
        import traceback
        traceback.print_exc()
        return []

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

def main():
    duration = 5  # seconds
    audio_result = record_audio(duration=duration)
    if audio_result is None:
        return
    audio_data, fs = audio_result

    detections = analyze_audio(audio_data, fs)
    for det in detections:
        species = det["common_name"]
        scientific_name = det["scientific_name"]
        confidence = round(det["confidence"], 2)
        rarity = det["rarity"]
        image_url = det["image_url"]
        print(f"Detected: {species} ({scientific_name}), Confidence: {confidence}, Rarity: {rarity}, Image URL: {image_url}")

if __name__ == "__main__":
    main()
