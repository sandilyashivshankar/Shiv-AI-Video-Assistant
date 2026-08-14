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
            parts = parsed.path.strip("/").split("/")
            return parts[1] if len(parts) > 1 else ""
        if parsed.path.startswith("/embed/"):
            parts = parsed.path.strip("/").split("/")
            return parts[1] if len(parts) > 1 else ""
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
        path.write_bytes(base64.b64decode(str(encoded), validate=True))
        return str(path)
    except Exception as exc:
        raise RuntimeError("YOUTUBE_COOKIES_B64 is not valid base64 cookie data.") from exc


def _youtube_options(output_template: str, player_clients: list[str]) -> dict:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "extractor_args": {"youtube": {"player_client": player_clients}},
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
    }
    cookies = _cookies_file()
    if cookies:
        opts["cookiefile"] = cookies
    return opts


def _fetch_youtube_transcript(url: str) -> str | None:
    if YouTubeTranscriptApi is None:
        return None
    video_id = _youtube_video_id(url)
    if not video_id:
        return None
    api = YouTubeTranscriptApi()
    for languages in (["en", "hi"], ["en"], ["hi"]):
        try:
            transcript = api.fetch(video_id, languages=languages)
            parts = []
            for snippet in transcript:
                text = getattr(snippet, "text", "").strip()
                if text:
                    parts.append(text)
            text = " ".join(parts).strip()
            if text:
                output = DOWNLOAD_DIR / f"youtube_{video_id}_transcript.txt"
                output.write_text(text, encoding="utf-8")
                return str(output)
        except Exception:
            continue
    return None


def download_youtube_audio(url: str) -> str:
    _ffmpeg()
    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
    profiles = [["android_vr"], ["web_safari"], ["web_embedded"]]
    errors = []

    for clients in profiles:
        try:
            label = ",".join(clients)
            print(f"Trying YouTube client: {label}")
            with yt_dlp.YoutubeDL(_youtube_options(output_template, clients)) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded = Path(ydl.prepare_filename(info)).with_suffix(".wav")
            if downloaded.exists():
                return str(downloaded)
            title = _safe_filename(info.get("title", "youtube_audio"))
            matches = sorted(DOWNLOAD_DIR.glob(f"{title}*.wav"))
            if matches:
                return str(matches[-1])
            errors.append(f"{label}: WAV output was not found")
        except Exception as exc:
            errors.append(f"{','.join(clients)}: {exc}")
            print(f"YouTube client {','.join(clients)} failed: {exc}")

    # YouTube can block Streamlit Cloud media downloads while still exposing captions.
    transcript_path = _fetch_youtube_transcript(url)
    if transcript_path:
        return transcript_path

    details = "\n".join(errors[-3:])
    raise RuntimeError(
        "YouTube blocked the media download from the Streamlit Cloud server "
        "and no accessible transcript was found. Upload the video/audio file "
        "for guaranteed processing, or configure authenticated YouTube cookies "
        "in Streamlit Secrets if you control the account.\n\nDetails:\n" + details
    )


def convert_to_wav(input_path: str) -> str:
    ffmpeg = _ffmpeg()
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    output_path = str(Path(input_path).with_name(Path(input_path).stem + "_converted.wav"))
    result = subprocess.run([
        ffmpeg, "-y", "-i", input_path, "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", output_path,
    ], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr[-2000:]}")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    ffmpeg = _ffmpeg()
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")
    output_pattern = f"{wav_path}_chunk_%03d.wav"
    result = subprocess.run([
        ffmpeg, "-y", "-i", wav_path, "-f", "segment",
        "-segment_time", str(chunk_minutes * 60), "-reset_timestamps", "1",
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output_pattern,
    ], capture_output=True, text=True)
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

        # A transcript is a valid processing source. transcribe_all() consumes it directly.
        if result_path.lower().endswith(".txt"):
            print("YouTube media blocked; using available transcript directly.")
            return [result_path]
        wav_path = result_path
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
