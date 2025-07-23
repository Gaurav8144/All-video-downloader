from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import uuid

app = FastAPI()

# Allow CORS (for frontend compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (HTML, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Homepage serving index.html
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Video download route
@app.post("/download")
async def download_video(url: str = Form(...)):
    try:
        video_id = str(uuid.uuid4())
        output_path = f"downloads/{video_id}.%(ext)s"

        ydl_opts = {
            'outtmpl': output_path,
            'format': 'mp4',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return FileResponse(filename, media_type='video/mp4', filename=os.path.basename(filename))

    except Exception as e:
        return {"error": str(e)}
