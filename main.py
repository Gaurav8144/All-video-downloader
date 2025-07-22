from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend HTML
@app.get("/")
async def serve_home():
    return FileResponse("index.html")

# Data model for link input
class LinkRequest(BaseModel):
    url: str

# POST endpoint to download video
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

        # Make downloadable link
        file_url = f"/downloads/{os.path.basename(filename)}"
        return {"status": "success", "file_url": file_url}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Serve downloaded files
@app.get("/downloads/{file_name:path}")
async def get_file(file_name: str):
    file_path = os.path.join("downloads", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"message": "File not found"})
