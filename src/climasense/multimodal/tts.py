"""Text-to-speech output for farmer-friendly voice responses.

Uses gTTS (Google Text-to-Speech) for multilingual audio generation.
Supports Swahili, Hindi, French, English, and 50+ other languages.
"""

import logging
import re
import tempfile
from pathlib import Path

from gtts import gTTS

logger = logging.getLogger(__name__)

# Language codes for common farmer languages
LANGUAGE_MAP = {
    "english": "en",
    "swahili": "sw",
    "hindi": "hi",
    "french": "fr",
    "arabic": "ar",
    "portuguese": "pt",
    "spanish": "es",
    "amharic": "am",
    "yoruba": "yo",
    "hausa": "ha",
    "igbo": "ig",
    "bengali": "bn",
    "tamil": "ta",
    "telugu": "te",
    "urdu": "ur",
}


def detect_language_code(text: str, default: str = "en") -> str:
    """Detect language from text or return default.

    Uses simple heuristics for common cases. For production,
    the agent's language detection from Gemma 4 should be preferred.
    """
    # Check for Swahili markers
    sw_words = {"habari", "shamba", "mazao", "mvua", "mimi", "ninayo", "mahindi", "nyanya", "udongo"}
    words = set(text.lower().split())
    if len(words & sw_words) >= 2:
        return "sw"

    # Check for Hindi (Devanagari script)
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"

    # Check for French markers
    fr_words = {"je", "les", "mes", "mon", "une", "des", "est", "sont", "cette", "avec"}
    if len(words & fr_words) >= 3:
        return "fr"

    # Check for Arabic script
    if re.search(r'[\u0600-\u06FF]', text):
        return "ar"

    return default


def clean_text_for_speech(text: str) -> str:
    """Clean markdown and formatting from text for natural speech.

    Removes markdown headers, bold/italic markers, bullet symbols,
    and other formatting that sounds awkward when read aloud.
    """
    # Remove markdown headers
    text = re.sub(r'#{1,6}\s*', '', text)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # Remove bullet points
    text = re.sub(r'^[\s]*[-*+]\s', '', text, flags=re.MULTILINE)
    # Remove numbered list formatting (keep the text)
    text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove excessive whitespace
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


def text_to_speech(
    text: str,
    output_path: str | Path | None = None,
    lang: str | None = None,
    slow: bool = False,
) -> Path:
    """Convert text to speech audio file.

    Args:
        text: Text to convert to speech.
        output_path: Output file path. If None, creates a temp file.
        lang: Language code (e.g., 'en', 'sw', 'hi'). Auto-detected if None.
        slow: Speak slowly (useful for non-native speakers).

    Returns:
        Path to the generated MP3 audio file.
    """
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        raise ValueError("No text to convert after cleaning")

    if lang is None:
        lang = detect_language_code(cleaned)

    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".mp3", prefix="climasense_tts_"))
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        tts = gTTS(text=cleaned, lang=lang, slow=slow)
        tts.save(str(output_path))
        logger.info("TTS audio saved: %s (lang=%s, %d chars)", output_path, lang, len(cleaned))
        return output_path

    except Exception as e:
        logger.error("TTS failed (lang=%s): %s", lang, e)
        # Fallback to English if language not supported
        if lang != "en":
            logger.info("Falling back to English TTS")
            tts = gTTS(text=cleaned, lang="en", slow=slow)
            tts.save(str(output_path))
            return output_path
        raise


def text_to_speech_chunked(
    text: str,
    output_dir: str | Path,
    lang: str | None = None,
    max_chars: int = 3000,
) -> list[Path]:
    """Convert long text to multiple audio files, split at paragraph boundaries.

    gTTS has limits on text length. This splits long responses into
    manageable chunks at natural paragraph breaks.

    Args:
        text: Full text to convert.
        output_dir: Directory for output files.
        lang: Language code. Auto-detected if None.
        max_chars: Max characters per chunk.

    Returns:
        List of paths to generated audio files, in order.
    """
    cleaned = clean_text_for_speech(text)
    if lang is None:
        lang = detect_language_code(cleaned)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split at paragraph boundaries
    paragraphs = cleaned.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current.strip():
        chunks.append(current.strip())

    paths = []
    for i, chunk in enumerate(chunks):
        path = output_dir / f"response_{i:02d}.mp3"
        text_to_speech(chunk, output_path=path, lang=lang)
        paths.append(path)

    return paths
