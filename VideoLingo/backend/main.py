from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import asyncio
import shutil
from dotenv import load_dotenv

load_dotenv()

from services import yt_downloader, gemini_ai, tts_generator

app = FastAPI(title="VideoLingo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ──────────────── Models ──────────────────
class FullPipelineRequest(BaseModel):
    url: str
    target_language: str = "vi"

class DownloadRequest(BaseModel):
    url: str

class TranscribeRequest(BaseModel):
    audio_filename: str
    target_language: str = "vi"

class TtsRequest(BaseModel):
    text: str
    lang: str = "vi"
    voice: str = "banmai"


class TranslateTextRequest(BaseModel):
    text: str
    source_language: str = "auto"
    target_language: str = "vi"


class RenameRequest(BaseModel):
    old_filename: str
    new_filename: str


# ──────────────── Helpers ──────────────────
def save_metadata(session_id: str, title: str, transcription: str, translation: str, 
                  audio_tts_filename: str, source_audio_filename: str):
    """Save session metadata as JSON in static/."""
    meta = {
        "session_id": session_id,
        "title": title,
        "transcription": transcription,
        "translation": translation,
        "tts_audio": audio_tts_filename,
        "source_audio": source_audio_filename,
    }
    meta_path = os.path.join("static", f"{session_id}_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta_path


# ──────────────── Endpoints ──────────────────
@app.get("/")
def read_root():
    return {"message": "Welcome to VideoLingo API"}


@app.post("/api/process-url")
async def process_video_url(req: FullPipelineRequest):
    """Full auto pipeline: Download → Transcribe+Translate → TTS. Streams SSE events."""
    async def event_generator():
        try:
            import uuid
            session_id = str(uuid.uuid4())[:8]
            
            yield f"data: {json.dumps({'status': 'processing', 'step': 'downloading', 'message': 'Tải video từ YouTube...'})}\n\n"
            result = await asyncio.to_thread(yt_downloader.download_audio, req.url)
            if not result:
                raise Exception("Không thể tải video. Kiểm tra lại URL.")
            audio_path = result['audio_path']
            title = result['title']
            source_filename = result['audio_filename']

            yield f"data: {json.dumps({'status': 'processing', 'step': 'transcribing', 'message': f'AI đang phiên dịch: {title[:50]}...'})}\n\n"
            transcription, translation = await asyncio.to_thread(
                gemini_ai.process_audio, audio_path, target_lang=req.target_language
            )

            yield f"data: {json.dumps({'status': 'processing', 'step': 'tts', 'message': 'Đang tạo giọng đọc tiếng Việt...'})}\n\n"
            tts_filename = await tts_generator.generate_tts(translation, output_dir="static", lang="vi")

            # Save metadata
            save_metadata(session_id, title, transcription, translation, tts_filename, source_filename)
            
            result_data = {
                "status": "success",
                "session_id": session_id,
                "title": title,
                "original_text": transcription,
                "translated_text": translation,
                "audio_url": f"/static/{tts_filename}",
                "source_audio_url": f"/static/{source_filename}",
                "metadata_url": f"/static/{session_id}_metadata.json",
            }
            yield f"data: {json.dumps(result_data)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/download-only")
async def download_only(req: DownloadRequest):
    """Download audio only from a URL."""
    async def event_generator():
        try:
            yield f"data: {json.dumps({'status': 'processing', 'step': 'downloading', 'message': 'Đang tải audio từ YouTube...'})}\n\n"
            result = await asyncio.to_thread(yt_downloader.download_audio, req.url)
            if not result:
                raise Exception("Không thể tải video. Kiểm tra lại URL.")
            audio_filename = result['audio_filename']
            payload = {
                'status': 'success',
                'audio_filename': audio_filename,
                'title': result['title'],
                'duration': result['duration'],
                'audio_url': f'/static/{audio_filename}',
            }
            yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload a file directly and bypass yt-dlp downloading."""
    try:
        import uuid
        file_id = str(uuid.uuid4())
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
        safe_filename = f"{file_id}.{ext}"
        filepath = os.path.join("static", safe_filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "status": "success",
            "audio_filename": safe_filename,
            "title": file.filename,
            "duration": 0,
            "audio_url": f"/static/{safe_filename}",
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/rename-file")
async def rename_file_endpoint(req: RenameRequest):
    import re, uuid
    old_path = os.path.join("static", req.old_filename)
    if not os.path.exists(old_path) or ".." in req.old_filename:
        raise HTTPException(status_code=404, detail="File not found or invalid")
    
    # Clean new filename
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', req.new_filename.replace(' ', '_'))
    if not safe_name:
        safe_name = "audio"
    if not safe_name.endswith(".mp3"):
        safe_name += ".mp3"
        
    new_path = os.path.join("static", safe_name)
    try:
        # Avoid overwriting existing files
        if os.path.exists(new_path) and old_path != new_path:
            safe_name = f"{safe_name.replace('.mp3', '')}_{str(uuid.uuid4())[:4]}.mp3"
            new_path = os.path.join("static", safe_name)
            
        os.rename(old_path, new_path)
        return {
            "status": "success",
            "new_filename": safe_name,
            "new_url": f"/static/{safe_name}"
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe")
async def transcribe_audio(req: TranscribeRequest):
    """Transcribe and translate an existing audio file from static/."""
    audio_path = os.path.join("static", req.audio_filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"Audio file '{req.audio_filename}' not found in static/")
    try:
        transcription, translation = await asyncio.to_thread(
            gemini_ai.process_audio, audio_path, target_lang=req.target_language
        )
        return {
            "status": "success",
            "transcription": transcription,
            "translation": translation,
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts-only")
async def tts_only(req: TtsRequest):
    """Generate TTS audio from text."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        tts_filename = await tts_generator.generate_tts(req.text, output_dir="static", lang=req.lang, voice=req.voice)
        return {
            "status": "success",
            "audio_filename": tts_filename,
            "audio_url": f"/static/{tts_filename}",
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate-text")
async def translate_text_endpoint(req: TranslateTextRequest):
    """Translate plain text via Gemini."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        translated = await asyncio.to_thread(
            gemini_ai.translate_text,
            req.text.strip(),
            req.source_language,
            req.target_language,
        )
        return {
            "status": "success",
            "original_text": req.text.strip(),
            "translated_text": translated,
            "source_language": req.source_language,
            "target_language": req.target_language,
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/list-sessions")
async def list_sessions():
    """List all saved sessions metadata."""
    files = []
    for f in os.listdir("static"):
        if f.endswith("_metadata.json"):
            try:
                with open(os.path.join("static", f), encoding="utf-8") as fp:
                    data = json.load(fp)
                files.append(data)
            except:
                pass
    files.sort(key=lambda x: x.get("session_id", ""), reverse=True)
    return {"sessions": files}
