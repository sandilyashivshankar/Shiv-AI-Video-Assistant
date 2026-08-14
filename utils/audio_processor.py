import base64
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None


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


def _youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "youtu.be" in host:
        return parsed.path.strip("/").split("/")[0]

    if "youtube.com" in host:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [""])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

    return ""


def _is_youtube_url(url: str) -> bool:
    return bool(_youtube_video_id(url))


def _cookies_file() -> str | None:
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
    opts = {
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


def _fetch_youtube_transcript(url: str) -> str | None:
    """Fallback for Cloud deployments where YouTube blocks media downloads.

    This uses captions/transcripts rather than downloading the protected media.
    It is only a fallback: videos without an accessible transcript still require
    the normal yt-dlp path or an uploaded media file.
    """
    if YouTubeTranscriptApi is None:
        return None

    video_id = _youtube_video_id(url)
    if not video_id:
        return None

    api = YouTubeTranscriptApi()
    errors = []

    for languages in (["en", "hi"], ["en"], ["hi"]):
        try:
            transcript = api.fetch(video_id, languages=languages)
            text = " ".join(
                snippet.text.strip()
                for snippet in transcript
                if getattr(snippet, "text", "").strip()
            ).strip()

            if text:
                output = DOWNLOAD_DIR / f"youtube_{video_id}_transcript.txt"
                output.write_text(text, encoding="utf-8")
                return str(output)
        except Exception as exc:
            errors.append(str(exc))

    print("YouTube transcript fallback failed:", " | ".join(errors[-2:]))
    return None


def download_youtube_audio(url: str) -> str:
    """Download YouTube audio with cloud fallbacks and transcript fallback."""
    _ffmpeg()
    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    profiles = ["web_safari", "web_embedded", "tv"]
    errors = []

    for client in profiles:
        try:
            print(f"Trying YouTube client: {client}")
            opts = _youtube_options(output_template, client)

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded = Path(ydl.prepare_filename(info)).with_suffix(".wav")

            if downloaded.exists():
                return str(downloaded)

            title = _safe_filename(info.get("title", "youtube_audio"))
            matches = sorted(DOWNLOAD_DIR.glob(f"{title}*.wav"))
            if matches:
                return str(matches[-1])

            errors.append(f"{client}: WAV output was not found")

        except Exception as exc:
            errors.append(f"{client}: {exc}")
            print(f"YouTube client {client} failed: {exc}")

    # Important for Streamlit Cloud: YouTube may reject the data-center IP even
    # when the same URL works locally. Try captions before giving up.
    transcript_path = _fetch_youtube_transcript(url)
    if transcript_path:
        return transcript_path

    detail = "\n".join(errors[-3:])
    raise RuntimeError(
        "YouTube blocked media download from the Streamlit Cloud server and "
        "no accessible YouTube transcript was found. Upload the video/audio "
        "file instead, or configure authenticated cookies if you control the "
        "video account.\nDetails:\n" + detail
    )


def convert_to_wav(input_path: str) -> str:
    ffmpeg = _ffmpeg()

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = str(
        Path(input_path).with_name(
            Path(input_path).stem + "_converted.wav"
        )
    )

    command = [
        ffmpeg, "-y", "-i", input_path, "-vn",
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        output_path,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr[-2000:]}")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    ffmpeg = _ffmpeg()

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    chunk_seconds = chunk_minutes * 60
    output_pattern = f"{wav_path}_chunk_%03d.wav"

    command = [
        ffmpeg, "-y", "-i", wav_path,
        "-f", "segment", "-segment_time", str(chunk_seconds),
        "-reset_timestamps", "1", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", output_pattern,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg chunking failed: {result.stderr[-2000:]}")

    chunks = sorted(Path(wav_path).parent.glob(Path(output_pattern).name))
    if not chunks:
        raise RuntimeError("FFmpeg completed but no audio chunks were created.")

    return [str(path) for path in chunks]


def process_input(source: str) -> list:
    source = source.strip()

    if not source:
        raise ValueError("Input source cannot be empty.")

    if source.startswith(("http://", "https://")):
        if not _is_youtube_url(source):
            raise ValueError("Only YouTube URLs are supported for URL input.")

        print("Detected YouTube URL. Downloading audio...")
        result_path = download_youtube_audio(source)

        # Transcript fallback produces a text file, so it must not be passed
        # through FFmpeg/chunking.
        if result_path.lower().endswith(".txt"):
            return [result_path]

        wav_path = result_path
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
