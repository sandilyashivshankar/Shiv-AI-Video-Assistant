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
    """Load optional authenticated YouTube cookies from env/Streamlit Secrets."""
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
        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 is not valid base64 cookie data."
        ) from exc


def _youtube_options(output_template: str, player_clients: list[str]) -> dict:
    """Build a yt-dlp profile suitable for hosted/cloud environments."""
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
                "player_client": player_clients,
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
    """Try YouTube captions when Cloud media downloads are blocked."""
    if YouTubeTranscriptApi is None:
        return None

    video_id = _youtube_video_id(url)
    if not video_id:
        return None

    api = YouTubeTranscriptApi()

    language_sets = [
        ["en", "hi"],
        ["en"],
        ["hi"],
    ]

    for languages in language_sets:
        try:
            transcript = api.fetch(
                video_id,
                languages=languages,
            )

            parts = []
            for snippet in transcript:
                text = getattr(snippet, "text", "").strip()
                if text:
                    parts.append(text)

            text = " ".join(parts).strip()

            if text:
                output = (
                    DOWNLOAD_DIR
                    / f"youtube_{video_id}_transcript.txt"
                )

                output.write_text(
                    text,
                    encoding="utf-8",
                )

                return str(output)

        except Exception:
            continue

    return None


def download_youtube_audio(url: str) -> str:
    """Try authenticated/direct download, then a YouTube transcript fallback."""
    _ffmpeg()

    output_template = str(
        DOWNLOAD_DIR / "%(title)s.%(ext)s"
    )

    # Current yt-dlp documentation identifies android_vr and web_safari as
    # useful default clients. When authenticated cookies are available, yt-dlp
    # can use web-based clients with the session; otherwise the fallback clients
    # are tried without claiming to bypass YouTube authentication.
    profiles = [
        ["android_vr"],
        ["web_safari"],
        ["web_embedded"],
    ]

    errors = []

    for clients in profiles:
        try:
            label = ",".join(clients)
            print(f"Trying YouTube client: {label}")

            opts = _youtube_options(
                output_template,
                clients,
            )

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True,
                )

                downloaded = Path(
                    ydl.prepare_filename(info)
                ).with_suffix(".wav")

            if downloaded.exists():
                return str(downloaded)

            title = _safe_filename(
                info.get("title", "youtube_audio")
            )

            matches = sorted(
                DOWNLOAD_DIR.glob(
                    f"{title}*.wav"
                )
            )

            if matches:
                return str(matches[-1])

            errors.append(
                f"{label}: WAV output was not found"
            )

        except Exception as exc:
            errors.append(
                f"{','.join(clients)}: {exc}"
            )
            print(
                f"YouTube client {','.join(clients)} failed: {exc}"
            )

    # Cloud IPs may be blocked even when local browser downloads work.
    # A public caption track can still let the downstream AI pipeline work.
    transcript_path = _fetch_youtube_transcript(url)

    if transcript_path:
        return transcript_path

    details = "\n".join(errors[-3:])

    raise RuntimeError(
        "YouTube blocked the media download from the Streamlit Cloud server "
        "and no accessible transcript was found. This is a YouTube-side "
        "authentication/anti-bot restriction, not an FFmpeg or Python error. "
        "Upload the video/audio file for guaranteed processing, or configure "
        "your own authenticated YouTube cookies in Streamlit Secrets if you "
        "control the account.\n\n"
        f"Details:\n{details}"
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
            Path(input_path).stem
            + "_converted.wav"
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
            "FFmpeg conversion failed: "
            f"{result.stderr[-2000:]}"
        )

    return output_path


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10,
) -> list:
    """Split WAV audio into fixed-length WAV chunks using FFmpeg."""
    ffmpeg = _ffmpeg()

    if not os.path.isfile(wav_path):
        raise FileNotFoundError(
            f"WAV file not found: {wav_path}"
        )

    chunk_seconds = chunk_minutes * 60

    output_pattern = (
        f"{wav_path}_chunk_%03d.wav"
    )

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
            "FFmpeg chunking failed: "
            f"{result.stderr[-2000:]}"
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
    """Process a YouTube URL or local audio/video file."""
    source = source.strip()

    if not source:
        raise ValueError(
            "Input source cannot be empty."
        )

    if source.startswith(
        ("http://", "https://")
    ):

        if not _is_youtube_url(source):
            raise ValueError(
                "Only YouTube URLs are supported for URL input."
            )

        print(
            "Detected YouTube URL. "
            "Downloading audio..."
        )

        result_path = download_youtube_audio(
            source
        )

        # Caption fallback returns text directly. The current downstream
        # transcriber expects WAV files, so signal this explicitly instead of
        # passing a TXT file into FFmpeg/Whisper.
        if result_path.lower().endswith(".txt"):
            raise RuntimeError(
                "A YouTube transcript was found, but this deployment's "
                "current transcription pipeline expects audio chunks. "
                "Please upload the video/audio file, or enable transcript "
                "as a direct text-analysis path."
            )

        wav_path = result_path

    else:

        print(
            "Detected local file. "
            "Converting to WAV..."
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
