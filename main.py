from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
import subprocess
import threading
import time

app = FastAPI()

# Allow all origins for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to save downloaded videos
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Delete file after delay
def delete_file_later(path, delay=10):
    def remove():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=remove).start()

@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        return JSONResponse(content={"status": "error", "message": "URL is required"}, status_code=400)

    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        subprocess.run(["yt-dlp", "-o", filepath, url], check=True, timeout=60)
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"status": "error", "message": "Download failed"}, status_code=500)
    except subprocess.TimeoutExpired:
        return JSONResponse(content={"status": "error", "message": "Download timed out"}, status_code=500)

    delete_file_later(filepath, delay=10)

    return JSONResponse(content={"status": "success", "file_url": f"/video/{filename}"})


@app.get("/video/{filename}")
async def get_video(filename: str):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="video/mp4", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")
