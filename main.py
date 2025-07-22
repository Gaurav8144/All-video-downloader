from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

# CORS (browser frontend ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML file serve karne ke liye
@app.get("/")
async def serve_home():
    return FileResponse("index.html")

# Model for incoming request
class LinkRequest(BaseModel):
    url: str

@app.post("/download")
async def download_video(link: LinkRequest):
    url = link.url
    try:
        output_dir = "downloads"
        os.makedirs(output_dir, exist_ok=True)
        ydl_opts = {
            "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
            "format": "best",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_path = os.path.abspath(filename)
        rel_path = "/" + os.path.relpath(file_path)
        return {"status": "success", "file_url": rel_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Video file serve karne ke liye
@app.get("/downloads/{file_name:path}")
async def get_file(file_name: str):
    file_path = os.path.join("downloads", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"message": "File not found"})
