# main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from bark import generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
import requests, uuid, os, subprocess

app = FastAPI()
preload_models()

class InputData(BaseModel):
    text: str
    background_query: str

@app.post("/generate")
async def generate_video(data: InputData):
    try:
        # Bark: Generate Audio from Text
        audio_array = generate_audio(data.text)
        audio_path = f"/tmp/{uuid.uuid4()}.wav"
        write_wav(audio_path, 22050, audio_array)

        # Pexels: Download background video
        pexels_api_key = os.getenv("PEXELS_API_KEY")
        headers = {"Authorization": pexels_api_key}
        r = requests.get(
            f"https://api.pexels.com/videos/search?query={data.background_query}&per_page=1",
            headers=headers
        )
        video_url = r.json()['videos'][0]['video_files'][0]['link']
        video_path = f"/tmp/{uuid.uuid4()}.mp4"
        with open(video_path, "wb") as f:
            f.write(requests.get(video_url).content)

        # FFmpeg: Merge audio and video
        output_path = f"/tmp/{uuid.uuid4()}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
        ], check=True)

        # OPTIONAL: Upload video somewhere and return URL
        return {"status": "success", "video_path": output_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}
      
