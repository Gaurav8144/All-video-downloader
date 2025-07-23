from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import subprocess

app = FastAPI()

# CORS setup (for local testing or frontend interaction)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Ensure download folder exists
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.post("/download")
async def download_video(url: str = Form(...)):
    try:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        # Run yt-dlp to download the video
        subprocess.run(["yt-dlp", "-o", filepath, url], check=True)

        return {"filename": filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/video/{filename}")
async def get_video(filename: str):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return FileResponse(path=filepath, media_type='video/mp4', filename=filename)
    return JSONResponse(status_code=404, content={"error": "File not found"})
