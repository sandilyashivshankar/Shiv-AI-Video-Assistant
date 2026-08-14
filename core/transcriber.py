import os
import shutil
import subprocess
import tempfile

import requests
import whisper


# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We split each chunk into 25s pieces before sending.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError(
            "FFmpeg is not installed. Add 'ffmpeg' to packages.txt."
        )
    return path


def _audio_duration_ms(wav_path: str) -> int:
    """Return WAV duration in milliseconds using ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        # ffmpeg package normally provides ffprobe; fail clearly if not available.
        raise RuntimeError("ffprobe is not installed with FFmpeg.")

    result = subprocess.run(
        [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            wav_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Unable to inspect audio: {result.stderr[-1000:]}")

    return int(float(result.stdout.strip()) * 1000)


def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe")
    return result["text"]


def _send_to_sarvam(piece_path: str) -> str:
    """Send one <=30s WAV file to Sarvam and return the English transcript."""
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / Streamlit Secrets")

    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false",
        }
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def _make_sarvam_piece(source_path: str, start_seconds: int, duration_seconds: int, output_path: str) -> None:
    """Create a 16 kHz mono WAV piece with FFmpeg; avoids pydub/audioop entirely."""
    ffmpeg = _ffmpeg()

    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-ss", str(start_seconds),
            "-t", str(duration_seconds),
            "-i", source_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            output_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio slicing failed: {result.stderr[-2000:]}")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts <=30s audio. We split this chunk into
    25-second pieces with FFmpeg and send each separately.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / Streamlit Secrets")

    duration_ms = _audio_duration_ms(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    total_pieces = (duration_ms + piece_ms - 1) // piece_ms

    full_text = []

    with tempfile.TemporaryDirectory(prefix="sarvam_") as temp_dir:
        for i, start_ms in enumerate(range(0, duration_ms, piece_ms)):
            piece_path = os.path.join(temp_dir, f"piece_{i:04d}.wav")
            remaining_ms = duration_ms - start_ms
            duration_seconds = min(SARVAM_PIECE_SECONDS, max(1, (remaining_ms + 999) // 1000))

            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            _make_sarvam_piece(
                chunk_path,
                start_ms // 1000,
                duration_seconds,
                piece_path,
            )

            text = _send_to_sarvam(piece_path).strip()
            if text:
                full_text.append(text)

    return " ".join(full_text).strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = ""

    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)
        full_transcript += text + " "

    print("Transcription complete.")
    return full_transcript.strip()
