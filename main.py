from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve HTML
@app.get("/")
async def home():
    return FileResponse("index.html")

# Pydantic model for incoming JSON
class LinkRequest(BaseModel):
    url: str

@app.post("/download")
async def download_video(link: LinkRequest):
    url = link.url
    try:
        output_dir = "downloads"
        os.makedirs(output_dir, exist_ok=True)

        # Prepare yt-dlp options
        ydl_opts = {
            "outtmpl": f"{output_dir}/%(title).80s.%(ext)s",
            "format": "bv*+ba/best",
            "merge_output_format": "mp4",
        }

        # If cookies.txt exists, use it
        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Path to return to frontend
        rel_path = "/" + os.path.relpath(filename).replace("\\", "/")
        return {"status": "success", "file_url": rel_path}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Serve downloaded file
@app.get("/downloads/{file_name:path}")
async def get_file(file_name: str):
    file_path = os.path.join("downloads", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"message": "File not found"})
