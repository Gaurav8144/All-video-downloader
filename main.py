from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import yt_dlp
import uuid
import os

app = FastAPI()

# CORS middleware for frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route for test
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h2>✅ Backend is running!</h2><p>Send a POST request to <code>/download</code> to download video.</p>"

# Download route
@app.post("/download")
async def download_video(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            return JSONResponse(content={"status": "error", "message": "No URL provided."}, status_code=400)

        # Unique filename
        filename = f"{uuid.uuid4()}.mp4"
        output_path = f"downloads/{filename}"
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return {"status": "success", "file_url": f"/file/{filename}"}

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# File route to serve downloaded files
@app.get("/file/{filename}")
async def get_file(filename: str):
    file_path = f"downloads/{filename}"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename, media_type='video/mp4')
    return JSONResponse(content={"status": "error", "message": "File not found."}, status_code=404)
