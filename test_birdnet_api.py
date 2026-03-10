import os
import requests

# Absolute paths for Windows
AUDIO_FOLDER = r"C:\birdvoice-backend\bird_audio_files"  # .wav files yahan rakho
RESULT_FOLDER = r"C:\birdvoice-backend\birdnet_results"  # results yahan save honge
API_URL = "http://127.0.0.1:8000/identify"

# Ensure result folder exists
os.makedirs(RESULT_FOLDER, exist_ok=True)

def identify_bird(file_path):
    with open(file_path, "rb") as f:
        files = {"audio": (os.path.basename(file_path), f, "audio/wav")}
        try:
            response = requests.post(API_URL, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error while processing {file_path}: {e}")
            return None

def main():
    audio_files = [f for f in os.listdir(AUDIO_FOLDER) if f.lower().endswith(".wav")]

    if not audio_files:
        print("No .wav files found in AUDIO_FOLDER.")
        return

    for file_name in audio_files:
        file_path = os.path.join(AUDIO_FOLDER, file_name)
        print(f"Processing: {file_name}")
        result = identify_bird(file_path)
        if result:
            # Save JSON result
            result_file = os.path.join(RESULT_FOLDER, f"{file_name}.json")
            with open(result_file, "w", encoding="utf-8") as rf:
                import json
                json.dump(result, rf, indent=4)
            print(f"Result saved: {result_file}")
        else:
            print(f"Failed to process: {file_name}")

if __name__ == "__main__":
    main()
