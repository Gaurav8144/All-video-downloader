from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import subprocess
import threading
import time

app = FastAPI()

# Allow all CORS (Frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to save downloaded files temporarily
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Serve downloads folder as static files
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_FOLDER), name="downloads")

# Delete file after delay (e.g. 60 seconds)
def delete_file_later(path, delay=60):
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
        raise HTTPException(status_code=400, detail="URL is required")

    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # Download video using yt-dlp
        subprocess.run(["yt-dlp", "-o", filepath, url], check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": "Download failed", "details": str(e)}, status_code=500)

    # Schedule file deletion after 60 seconds
    delete_file_later(filepath, delay=60)

    # Return public URL
    file_url = f"/downloads/{filename}"
    return JSONResponse(content={
        "status": "success",
        "file_url": file_url
    })
