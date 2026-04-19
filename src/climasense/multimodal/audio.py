"""Audio input processing for voice-based farmer queries.

Gemma 4 E4B/E2B supports native audio input. This module handles:
1. Voice query transcription and understanding
2. Language detection for multilingual support
3. Audio loading from files or raw arrays
"""

import logging
from pathlib import Path

import numpy as np
import torch

logger = logging.getLogger(__name__)

# Default sample rate for Gemma 4 audio input
DEFAULT_SAMPLE_RATE = 16000

VOICE_QUERY_PROMPT = """\
Listen to this farmer's voice query carefully.

1. **Transcribe** the spoken words exactly
2. **Identify the language** spoken
3. **Extract the agricultural question or concern** being raised
4. **Identify urgency level**: routine / concerning / urgent

Respond in the same language as the farmer."""


def load_audio(audio_path: str | Path, target_sr: int = DEFAULT_SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """Load an audio file and resample to target sample rate.

    Args:
        audio_path: Path to audio file (WAV, MP3, FLAC, OGG, etc.).
        target_sr: Target sample rate (default 16000 for Gemma 4).

    Returns:
        Tuple of (audio_array, sample_rate).
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        import soundfile as sf
        audio, sr = sf.read(str(audio_path), dtype="float32")
    except Exception:
        import librosa
        audio, sr = librosa.load(str(audio_path), sr=None)

    # Convert stereo to mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample if needed
    if sr != target_sr:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    return audio.astype(np.float32), sr


def process_voice_query(
    audio_input,
    processor,
    model,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    prompt: str | None = None,
) -> dict:
    """Process a farmer's voice query using Gemma 4 E4B native audio.

    Args:
        audio_input: Audio as numpy array, file path (str/Path), or torch.Tensor.
        processor: Loaded Gemma 4 processor (E4B or E2B).
        model: Loaded Gemma 4 model with audio support.
        sample_rate: Sample rate of audio (default 16000).
        prompt: Custom prompt text (defaults to VOICE_QUERY_PROMPT).

    Returns:
        Dictionary with transcription, language, extracted query, and urgency.
    """
    # Load audio from file if path given
    if isinstance(audio_input, (str, Path)):
        audio_array, sample_rate = load_audio(audio_input)
    elif isinstance(audio_input, torch.Tensor):
        audio_array = audio_input.cpu().numpy()
    else:
        audio_array = np.asarray(audio_input, dtype=np.float32)

    if prompt is None:
        prompt = VOICE_QUERY_PROMPT

    # Build the chat template with audio token
    messages = [
        {"role": "user", "content": [
            {"type": "audio", "audio": audio_array},
            {"type": "text", "text": prompt},
        ]}
    ]

    try:
        # Step 1: Get template text (places <|audio|> token)
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )

        # Step 2: Process text + audio features together
        inputs = processor(
            text=text,
            audio=[audio_array],
            sampling_rate=sample_rate,
            return_tensors="pt",
        )
        inputs = {k: v.to(model.device) if hasattr(v, "to") else v for k, v in inputs.items()}

        logger.info(
            "Audio processed: %d samples, %d tokens, features shape %s",
            len(audio_array),
            inputs["input_ids"].shape[1],
            inputs.get("input_features", torch.tensor([])).shape,
        )

        # Step 3: Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
            )

        new_tokens = outputs[0, inputs["input_ids"].shape[1]:]
        response = processor.decode(new_tokens, skip_special_tokens=True)

        return {
            "transcription": response,
            "audio_duration_s": len(audio_array) / sample_rate,
            "sample_rate": sample_rate,
            "model": model.config._name_or_path,
        }

    except Exception as e:
        logger.error("Audio processing failed: %s", e)
        return {
            "error": f"Audio processing failed: {e}",
            "audio_duration_s": len(audio_array) / sample_rate,
            "fallback": "Please type your question instead, or share a photo of your crop.",
        }


def transcribe_audio(
    audio_input,
    processor,
    model,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> str:
    """Simple transcription — returns just the text.

    Args:
        audio_input: Audio as numpy array, file path, or tensor.
        processor: Loaded Gemma 4 processor.
        model: Loaded Gemma 4 model.
        sample_rate: Audio sample rate.

    Returns:
        Transcribed text string.
    """
    result = process_voice_query(
        audio_input, processor, model, sample_rate,
        prompt="Transcribe this audio exactly. Output only the transcription, nothing else.",
    )
    return result.get("transcription", result.get("error", ""))
