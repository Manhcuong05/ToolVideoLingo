import os
from google import genai

def process_audio(audio_path: str, source_lang: str = "auto", target_lang: str = "vi") -> tuple[str, str]:
    """Upload audio to Gemini and request transcription and translation.
    Returns (transcription, translation).
    If source language equals target language, translation will be same as transcription.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
        
    client = genai.Client(api_key=api_key)
    
    lang_names = {
        "vi": "Vietnamese", "en": "English", "zh": "Chinese",
        "ja": "Japanese", "ko": "Korean", "fr": "French",
        "de": "German", "es": "Spanish", "th": "Thai"
    }
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    try:
        audio_file = client.files.upload(file=audio_path, config={'display_name': os.path.basename(audio_path)})
        
        prompt = f"""
        Please perform two tasks based on this audio file:
        1. Auto-detect the spoken language and transcribe the speech into text accurately.
        2. If the detected language is NOT {target_lang_name}, translate the transcribed text into {target_lang_name}.
           If the detected language IS ALREADY {target_lang_name}, return the transcription as-is (do NOT translate to another language).
        
        Format your response exactly as follows, with no extra commentary:
        ---TRANSCRIPTION---
        [Insert full transcription here]
        ---TRANSLATION---
        [Insert translation here, or repeat transcription if already in {target_lang_name}]
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_file, prompt]
        )
        
        text = response.text
        
        transcription = ""
        translation = ""
        
        if "---TRANSCRIPTION---" in text and "---TRANSLATION---" in text:
            parts = text.split("---TRANSLATION---")
            transcription = parts[0].replace("---TRANSCRIPTION---", "").strip()
            translation = parts[1].strip()
        else:
            transcription = text
            translation = text
            
        return transcription, translation
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise

def transcribe_only(audio_path: str) -> str:
    """Transcribe audio to text without translation."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    client = genai.Client(api_key=api_key)
    try:
        audio_file = client.files.upload(file=audio_path, config={'display_name': os.path.basename(audio_path)})
        prompt = "Transcribe all the spoken speech in this audio faithfully. Return only the transcription text, nothing else."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[audio_file, prompt])
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise


def translate_text(text: str, source_lang: str = "auto", target_lang: str = "vi") -> str:
    """Translate plain text using Gemini. Returns the translated string."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    client = genai.Client(api_key=api_key)

    lang_names = {
        "auto": "auto-detect", "vi": "Vietnamese", "en": "English",
        "zh": "Chinese (Simplified)", "ja": "Japanese", "ko": "Korean",
        "fr": "French", "de": "German", "es": "Spanish",
        "th": "Thai", "ru": "Russian", "pt": "Portuguese",
        "it": "Italian", "ar": "Arabic",
    }
    src_desc = f"from {lang_names.get(source_lang, source_lang)} " if source_lang != "auto" else ""
    tgt_name = lang_names.get(target_lang, target_lang)

    prompt = (
        f"Translate the following text {src_desc}into {tgt_name}. "
        "Return ONLY the translated text — no commentary, no explanation, no quotation marks.\n\n"
        f"{text}"
    )

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini translate_text Error: {e}")
        raise
