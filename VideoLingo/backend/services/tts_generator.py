import uuid
import os
import asyncio
import subprocess
import re
import time
import urllib.request
import urllib.error
import ssl
from concurrent.futures import ThreadPoolExecutor

# ── FPT.AI voice codes ─────────────────────────────────────────────────────────
FPT_VOICES = {
    "banmai":     "Ban Mai (Nữ Bắc) ⭐",
    "leminh":     "Lê Minh (Nam Bắc)",
    "myan":       "Mỹ An (Nữ Trung)",
    "giahuy":     "Gia Huy (Nam Trung)",
    "ngoclam":    "Ngọc Lam (Nữ Trung)",
    "minhquang":  "Minh Quang (Nam Nam)",
    "linhsan":    "Linh San (Nữ Nam)",
    "lannhi":     "Lan Nhi (Nữ Nam)",
}

# Edge-TTS fallback voices (used when FPT key not set)
EDGE_VOICES = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
}

FPT_MAX_CHARS = 2500  # safe under FPT.AI's 3000 char limit
_executor = ThreadPoolExecutor(max_workers=4)

# Allow self-signed / unverified SSL (some environments block cert verification)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _split_text(text: str, max_chars: int = FPT_MAX_CHARS) -> list:
    """Split text into chunks <= max_chars, breaking on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip() if current else sentence
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i + max_chars])
                current = ""
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks


def _fpt_post_sync(text: str, api_key: str, voice: str) -> str:
    """Synchronously POST text to FPT.AI TTS, return the async MP3 URL."""
    import json as _json
    req = urllib.request.Request(
        "https://api.fpt.ai/hmi/tts/v5",
        data=text.encode("utf-8"),
        headers={
            "api-key": api_key,
            "speed": "",
            "voice": voice,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20, context=_ssl_ctx) as resp:
        body = resp.read().decode("utf-8")
    data = _json.loads(body)
    if data.get("error") != 0:
        raise RuntimeError(f"FPT.AI error: {data}")
    return data["async"]


def _download_when_ready_sync(async_url: str, output_path: str, max_wait: int = 40) -> None:
    """Poll async_url until audio is ready, then save to output_path."""
    for _ in range(max_wait):
        time.sleep(1)
        try:
            req = urllib.request.Request(async_url)
            with urllib.request.urlopen(req, timeout=15, context=_ssl_ctx) as resp:
                ct = resp.headers.get("Content-Type", "")
                body = resp.read()
                if "audio" in ct or "octet-stream" in ct or body[:3] == b"ID3" or body[:2] == b"\xff\xfb":
                    with open(output_path, "wb") as f:
                        f.write(body)
                    return
        except Exception:
            pass  # Not ready yet, keep polling
    raise TimeoutError("FPT.AI audio not ready after 40s")


def _fpt_tts_sync(text: str, output_path: str, api_key: str, voice: str) -> None:
    """Full synchronous FPT.AI TTS call with chunking support."""
    chunks = _split_text(text)
    print(f"[TTS] FPT.AI: {len(chunks)} chunk(s) for {len(text)} chars, voice={voice}")

    if len(chunks) == 1:
        async_url = _fpt_post_sync(chunks[0], api_key, voice)
        _download_when_ready_sync(async_url, output_path)
    else:
        tmp_files = []
        output_dir = os.path.dirname(output_path) or "."
        try:
            for chunk in chunks:
                tmp_path = os.path.join(output_dir, f"_chunk_{uuid.uuid4().hex}.mp3")
                tmp_files.append(tmp_path)
                async_url = _fpt_post_sync(chunk, api_key, voice)
                _download_when_ready_sync(async_url, tmp_path)
                time.sleep(0.3)

            # Concatenate with ffmpeg
            list_file = os.path.join(output_dir, f"_list_{uuid.uuid4().hex}.txt")
            with open(list_file, "w") as f:
                for p in tmp_files:
                    f.write(f"file '{os.path.abspath(p)}'\n")
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", list_file, "-c", "copy", output_path],
                check=True, capture_output=True
            )
            os.remove(list_file)
        finally:
            for f in tmp_files:
                if os.path.exists(f):
                    os.remove(f)


async def _fpt_tts(text: str, output_path: str, voice: str = "banmai") -> None:
    """Async wrapper around synchronous FPT.AI calls (run in thread pool)."""
    api_key = os.getenv("FPT_TTS_API_KEY", "")
    if not api_key:
        raise ValueError("FPT_TTS_API_KEY is not set")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _fpt_tts_sync, text, output_path, api_key, voice)


async def _edge_tts(text: str, output_path: str, lang: str = "vi") -> None:
    """Fallback: use edge-tts (Microsoft Neural TTS, no API key needed)."""
    import edge_tts
    voice = EDGE_VOICES.get(lang, "vi-VN-HoaiMyNeural")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def generate_tts(
    text: str,
    output_dir: str = "static",
    lang: str = "vi",
    voice: str = "banmai",
) -> str:
    """Generate TTS audio.
    - Short text (≤2500 chars) + FPT key → FPT.AI (natural Vietnamese voices)
    - Long text or no key → edge-tts (unlimited, free forever)
    Returns the output filename (not full path).
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"tts_{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_dir, filename)

    api_key = os.getenv("FPT_TTS_API_KEY", "")
    use_fpt = api_key and len(text) <= FPT_MAX_CHARS

    try:
        if use_fpt:
            print(f"[TTS] Using FPT.AI, voice={voice}, chars={len(text)}")
            await _fpt_tts(text, output_path, voice=voice)
        else:
            if api_key and len(text) > FPT_MAX_CHARS:
                print(f"[TTS] Text too long ({len(text)} chars) → using edge-tts for speed")
            else:
                print("[TTS] No FPT key → using edge-tts")
            await _edge_tts(text, output_path, lang=lang)
        return filename
    except Exception as e:
        print(f"[TTS] Error with primary provider: {e}, falling back to edge-tts")
        try:
            await _edge_tts(text, output_path, lang=lang)
            return filename
        except Exception as e2:
            print(f"[TTS] edge-tts also failed: {e2}")
            raise

