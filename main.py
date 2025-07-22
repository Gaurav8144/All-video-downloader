from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

# CORS for frontend JS access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home Route - serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("<h2>⚠️ index.html not found!</h2>", status_code=500)

# Request model
class LinkRequest(BaseModel):
    url: str

# Video download route
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

        rel_path = "/" + os.path.relpath(filename)
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
