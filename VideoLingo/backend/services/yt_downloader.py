import yt_dlp
import os
import uuid
import base64
import tempfile

def _get_cookies_file() -> str | None:
    """Decode YOUTUBE_COOKIES_B64 env var into a temp file and return its path."""
    b64 = os.environ.get("YOUTUBE_COOKIES_B64")
    if not b64:
        return None
    try:
        content = base64.b64decode(b64).decode("utf-8")
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"Warning: Failed to decode YOUTUBE_COOKIES_B64: {e}")
        return None

def download_audio(url: str, output_dir: str = "static") -> dict:
    """Download audio from a given URL using yt-dlp."""
    os.makedirs(output_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{file_id}.%(ext)s")
    
    video_info = {}
    cookies_file = _get_cookies_file()
    
    ydl_opts = {
        # Use a broad format that accepts any audio stream
        'format': 'bestaudio/best/worst',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': False,
        'nocheckcertificate': True,
        'retries': 5,
        'fragment_retries': 5,
        # Don't download playlists — just the single video
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extractor_args': {
            'youtubetab': {
                'skip': ['authcheck'],
            },
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'web'],
                'player_skip': ['js', 'configs']
            }
        },
    }

    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file
        print("Using YouTube cookies from env var.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_info['title'] = info.get('title', 'Unknown')
            video_info['duration'] = info.get('duration', 0)
        audio_path = os.path.join(output_dir, f"{file_id}.mp3")
        return {
            'audio_path': audio_path,
            'audio_filename': f"{file_id}.mp3",
            'title': video_info.get('title', 'Unknown'),
            'duration': video_info.get('duration', 0),
        }
    except Exception as e:
        print(f"Error downloading video: {e}")
        raise
    finally:
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)
