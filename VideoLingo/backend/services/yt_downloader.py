import yt_dlp
import os
import uuid

def download_audio(url: str, output_dir: str = "static") -> dict:
    """Download audio from a given URL using yt-dlp.
    Returns dict with 'audio_path' and 'title'.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    output_template = os.path.join(output_dir, f"{file_id}.%(ext)s")
    
    video_info = {}
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        # Cloud server bypass options
        'nocheckcertificate': True,
        'no_warnings': False,
        'retries': 5,
        'fragment_retries': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_info['title'] = info.get('title', 'Unknown')
            video_info['duration'] = info.get('duration', 0)
            video_info['uploader'] = info.get('uploader', '')
        audio_path = os.path.join(output_dir, f"{file_id}.mp3")
        return {
            'audio_path': audio_path,
            'audio_filename': f"{file_id}.mp3",
            'title': video_info.get('title', 'Unknown'),
            'duration': video_info.get('duration', 0),
        }
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None
