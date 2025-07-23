from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import subprocess
import threading
import time

app = FastAPI()

# Allow all CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads folder if not exists
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Mount downloads as static so video can be served
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_FOLDER), name="downloads")

# Mount static folder to serve HTML and other static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root path "/"
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

# Delete file after delay (e.g. 60 seconds)
def delete_file_later(path, delay=60):
    def remove():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=remove).start()

# Video download endpoint
@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # Use yt-dlp to download the video
        subprocess.run(["yt-dlp", "-o", filepath, url], check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(content={"error": "Download failed", "details": str(e)}, status_code=500)

    # Schedule file deletion
    delete_file_later(filepath, delay=60)

    # Return file URL to frontend
    file_url = f"/downloads/{filename}"
    return JSONResponse(content={
        "status": "success",
        "file_url": file_url
    })
