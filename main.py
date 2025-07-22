from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import uuid
import os
import threading
import time

app = FastAPI()

# CORS (in case you want frontend from other origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(__file__)
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
HTML_FILE = os.path.join(BASE_DIR, "index.html")

# Create downloads folder if it doesn't exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Serve downloads folder statically
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_FOLDER), name="downloads")

# Serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        return f.read()


# Automatically delete file after delay
def delete_file_later(path, delay=30):
    def delete():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=delete).start()


# Download Endpoint
@app.post("/download")
async def download_video(request: Request):
    try:
        data = await request.json()
        url = data.get("url")

        if not url:
            return JSONResponse({"status": "error", "message": "URL is missing"}, status_code=400)

        filename = str(uuid.uuid4()) + ".mp4"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        print(f"[INFO] Downloading: {url}")
        print(f"[INFO] Saving as: {filepath}")

        result = subprocess.run(
            ["yt-dlp", "-f", "best", "-o", filepath, url],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("[ERROR]", result.stderr)
            return JSONResponse({"status": "error", "message": result.stderr.strip()}, status_code=500)

        delete_file_later(filepath)

        return JSONResponse({
            "status": "success",
            "file_url": f"/downloads/{filename}"
        })

    except Exception as e:
        print("[EXCEPTION]", str(e))
        return JSONResponse({"status": "error", "message": "Unknown error occurred."}, status_code=500)
