from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import subprocess
import threading
import time

app = FastAPI()

# ✅ CORS (Allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for simplicity
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Create downloads folder if not exists
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ✅ Serve static files (index.html and assets)
app.mount("/", StaticFiles(directory=".", html=True), name="static")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")  # ✅ NEW LINE

# ✅ Auto-delete downloaded file after delay
def delete_file_later(path, delay=20):
    def remove():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=remove).start()

# ✅ Video downloader route
@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Generate unique filename
    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        result = subprocess.run(
            ["yt-dlp", "-f", "best", "-o", filepath, url],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            content={"status": "error", "message": e.stderr.strip() or "Download failed"},
            status_code=500
        )

    # Schedule file deletion
    delete_file_later(filepath, delay=20)

    return JSONResponse({
        "status": "success",
        "file_url": f"/downloads/{filename}"
    })
