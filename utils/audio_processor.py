import base64
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp


DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloades"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("FFmpeg is not installed. Add 'ffmpeg' to packages.txt.")
    return path


def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(".")
    return name[:180] or "youtube_audio"


def _is_youtube_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def _cookies_file() -> str | None:
    """Optionally materialize YOUTUBE_COOKIES_B64 from Streamlit Secrets/env."""
    encoded = os.getenv("YOUTUBE_COOKIES_B64")
    if not encoded:
        try:
            import streamlit as st
            encoded = st.secrets.get("YOUTUBE_COOKIES_B64")
        except Exception:
            encoded = None

    if not encoded:
        return None

    path = DOWNLOAD_DIR / ".youtube_cookies.txt"
    try:
        path.write_bytes(base64.b64decode(str(encoded)))
        return str(path)
    except Exception as exc:
        raise RuntimeError("YOUTUBE_COOKIES_B64 is not valid base64 cookie data.") from exc


def _youtube_options(output_template: str, player_client: str) -> dict:
    """Build a YouTube profile optimized for hosted/cloud IPs."""
    opts = {
        # Prefer HLS-capable audio when available; web_safari HLS currently avoids
        # the GVS PO-token requirement for affected downloads.
        "format": "bestaudio[protocol=m3u8_native]/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "source_address": "0.0.0.0",
        "extractor_args": {
            "youtube": {
                "player_client": [player_client],
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    cookies = _cookies_file()
    if cookies:
        opts["cookiefile"] = cookies

    return opts


def download_youtube_audio(url: str) -> str:
    """Download YouTube audio with cloud-friendly client fallbacks."""
    _ffmpeg()

    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    # YouTube currently enforces Proof-of-Origin tokens for some clients.
    # web_safari can use HLS formats that do not currently require a GVS PO token;
    # web_embedded is a useful fallback for videos that permit embedding.
    profiles = [
        "web_safari",
        "web_embedded",
        "tv",
    ]

    errors = []

    for client in profiles:
        try:
            print(f"Trying YouTube client: {client}")

            opts = _youtube_options(
                output_template,
                client,
            )

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded = Path(
                    ydl.prepare_filename(info)
                ).with_suffix(".wav")

            if downloaded.exists():
                return str(downloaded)

            title = _safe_filename(
                info.get("title", "youtube_audio")
            )

            matches = sorted(
                DOWNLOAD_DIR.glob(f"{title}*.wav")
            )

            if matches:
                return str(matches[-1])

            errors.append(
                f"{client}: WAV output was not found"
            )

        except Exception as exc:
            errors.append(
                f"{client}: {exc}"
            )
            print(
                f"YouTube client {client} failed: {exc}"
            )

    detail = "\n".join(errors[-3:])

    raise RuntimeError(
        "YouTube rejected the download from the Streamlit Cloud server. "
        "This is commonly caused by YouTube's current anti-bot/Proof-of-Origin "
        "requirements or the application's data-center IP. "
        "The app tried multiple supported YouTube clients. "
        f"\nDetails:\n{detail}"
    )


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to mono 16 kHz WAV using FFmpeg."""
    ffmpeg = _ffmpeg()

    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    output_path = str(
        Path(input_path).with_name(
            Path(input_path).stem + "_converted.wav"
        )
    )

    command = [
        ffmpeg,
        "-y",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        output_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg conversion failed: {result.stderr[-2000:]}"
        )

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Split WAV audio into fixed-length WAV chunks using FFmpeg."""
    ffmpeg = _ffmpeg()

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAV file not found: {wav_path}"
        )

    chunk_seconds = chunk_minutes * 60
    output_pattern = f"{wav_path}_chunk_%03d.wav"

    command = [
        ffmpeg,
        "-y",
        "-i", wav_path,
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-reset_timestamps", "1",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        output_pattern,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg chunking failed: {result.stderr[-2000:]}"
        )

    chunks = sorted(
        Path(wav_path).parent.glob(
            Path(output_pattern).name
        )
    )

    if not chunks:
        raise RuntimeError(
            "FFmpeg completed but no audio chunks were created."
        )

    return [str(path) for path in chunks]


def process_input(source: str) -> list:
    """Download/convert input and return transcription-ready chunks."""
    source = source.strip()

    if not source:
        raise ValueError(
            "Input source cannot be empty."
        )

    if source.startswith(("http://", "https://")):
        if not _is_youtube_url(source):
            raise ValueError(
                "Only YouTube URLs are supported for URL input."
            )

        print(
            "Detected YouTube URL. Downloading audio..."
        )

        wav_path = download_youtube_audio(
            source
        )

    else:
        print(
            "Detected local file. Converting to WAV..."
        )

        wav_path = convert_to_wav(
            source
        )

    print("Chunking audio...")

    chunks = chunk_audio(
        wav_path
    )

    print(
        f"Audio ready — {len(chunks)} chunk(s) created."
    )

    return chunks
