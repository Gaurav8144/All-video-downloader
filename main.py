from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import os
import uuid
import subprocess

app = FastAPI()

# Create downloads folder if it doesn't exist
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# CORS setup (optional but recommended)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    try:
        with open("static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except:
        return HTMLResponse(content="<h1>Index file not found</h1>", status_code=404)

@app.post("/download")
async def download_video(request: Request):
    form = await request.form()
    url = form.get("url")
    if not url:
        return JSONResponse({"error": "URL is required"}, status_code=400)

    video_id = str(uuid.uuid4())
    output_path = f"downloads/{video_id}.mp4"

    try:
        # Download video using yt-dlp
        subprocess.run(["yt-dlp", "-o", output_path, url], check=True)
        return FileResponse(output_path, media_type="video/mp4", filename="video.mp4")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
