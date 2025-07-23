from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import subprocess
import threading
import time

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder for temporary video downloads
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Serve static files like index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve homepage from static/index.html
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Auto delete file after 10 sec
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
        raise HTTPException(status_code=400, detail="URL is required")

    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # yt-dlp command to download video
        subprocess.run(["yt-dlp", "-o", filepath, url], check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            content={"status": "error", "message": "Download failed", "details": str(e)},
            status_code=500,
        )

    delete_file_later(filepath, delay=10)

    # Return file URL (Render will host it on domain)
    return JSONResponse(content={
        "status": "success",
        "file_url": f"/downloaded/{filename}",
        "filename": filename
    })

# Serve downloaded video temporarily
@app.get("/downloaded/{filename}", response_class=FileResponse)
async def serve_file(filename: str):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
