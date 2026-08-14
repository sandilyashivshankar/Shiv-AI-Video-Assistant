import os
from pathlib import Path

import yt_dlp
from pydub import AudioSegment


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# YOUTUBE AUDIO DOWNLOAD
# ============================================================

def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL and convert it to WAV.

    Uses:
        - yt-dlp
        - Deno JavaScript runtime
        - android_vr YouTube client
        - FFmpegExtractAudio
    """

    if not url:
        raise ValueError("YouTube URL cannot be empty.")

    output_template = str(
        DOWNLOAD_DIR / "%(title)s.%(ext)s"
    )

    ydl_opts = {
        # Best available audio
        "format": "bestaudio/best",

        # Output filename
        "outtmpl": output_template,

        # Only download the requested video
        "noplaylist": True,

        # Don't download thumbnails, subtitles, etc.
        "skip_download": False,

        # Logging
        "quiet": False,
        "no_warnings": False,

        # ====================================================
        # YouTube JavaScript challenge solving
        # ====================================================

        "js_runtimes": {
            "deno": {}
        },

        # ====================================================
        # YouTube extractor configuration
        # ====================================================

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android_vr"
                ]
            }
        },

        # ====================================================
        # Convert downloaded audio to WAV
        # ====================================================

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            print("Downloading YouTube audio...")

            info = ydl.extract_info(
                url,
                download=True
            )

            if not info:
                raise RuntimeError(
                    "yt-dlp did not return video information."
                )

            downloaded_file = Path(
                ydl.prepare_filename(info)
            )

            # yt-dlp + FFmpeg changes extension to .wav
            wav_file = downloaded_file.with_suffix(".wav")

        # ====================================================
        # Verify generated WAV file
        # ====================================================

        if not wav_file.exists():

            # Some formats may produce a different
            # original extension. Search for matching WAV.

            possible_files = list(
                DOWNLOAD_DIR.glob(
                    f"{downloaded_file.stem}*.wav"
                )
            )

            if possible_files:
                wav_file = possible_files[0]

            else:
                raise FileNotFoundError(
                    "YouTube audio was downloaded, "
                    "but the WAV file could not be found."
                )

        print(
            f"YouTube audio downloaded successfully: "
            f"{wav_file}"
        )

        return str(wav_file)

    except yt_dlp.utils.DownloadError as e:

        error_message = str(e)

        if "403" in error_message:

            raise RuntimeError(
                "YouTube returned HTTP 403 Forbidden.\n\n"
                "Possible causes:\n"
                "1. YouTube requires a PO token.\n"
                "2. The selected YouTube client was rejected.\n"
                "3. YouTube temporarily restricted your IP.\n"
                "4. yt-dlp/EJS/Deno needs updating.\n\n"
                "Try updating yt-dlp and yt-dlp-ejs."
            ) from e

        raise RuntimeError(
            f"YouTube download failed:\n{error_message}"
        ) from e

    except Exception as e:

        raise RuntimeError(
            f"Unexpected YouTube download error:\n{str(e)}"
        ) from e


# ============================================================
# LOCAL AUDIO / VIDEO → WAV
# ============================================================

def convert_to_wav(input_path: str) -> str:
    """
    Convert a local audio/video file to:
        - WAV
        - mono
        - 16 kHz

    This format is suitable for speech recognition.
    """

    if not input_path:
        raise ValueError(
            "Input file path cannot be empty."
        )

    input_file = Path(input_path)

    if not input_file.exists():

        raise FileNotFoundError(
            f"Input file does not exist:\n{input_path}"
        )

    output_path = input_file.with_name(
        f"{input_file.stem}_converted.wav"
    )

    try:

        print(
            f"Converting file to WAV: {input_file}"
        )

        audio = AudioSegment.from_file(
            str(input_file)
        )

        # Speech recognition friendly format
        audio = (
            audio
            .set_channels(1)
            .set_frame_rate(16000)
        )

        audio.export(
            str(output_path),
            format="wav"
        )

        print(
            f"Conversion completed: {output_path}"
        )

        return str(output_path)

    except Exception as e:

        raise RuntimeError(
            f"Failed to convert audio/video to WAV:\n{str(e)}"
        ) from e


# ============================================================
# AUDIO CHUNKING
# ============================================================

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into smaller chunks.

    Default:
        10 minutes per chunk.
    """

    if not wav_path:
        raise ValueError(
            "WAV path cannot be empty."
        )

    wav_file = Path(wav_path)

    if not wav_file.exists():

        raise FileNotFoundError(
            f"WAV file does not exist:\n{wav_path}"
        )

    if chunk_minutes <= 0:

        raise ValueError(
            "chunk_minutes must be greater than 0."
        )

    try:

        print("Loading audio for chunking...")

        audio = AudioSegment.from_wav(
            str(wav_file)
        )

        chunk_ms = (
            chunk_minutes
            * 60
            * 1000
        )

        chunks = []

        for i, start in enumerate(
            range(
                0,
                len(audio),
                chunk_ms
            )
        ):

            chunk = audio[
                start:start + chunk_ms
            ]

            chunk_path = wav_file.with_name(
                f"{wav_file.stem}_chunk_{i}.wav"
            )

            chunk.export(
                str(chunk_path),
                format="wav"
            )

            chunks.append(
                str(chunk_path)
            )

        print(
            f"Created {len(chunks)} audio chunk(s)."
        )

        return chunks

    except Exception as e:

        raise RuntimeError(
            f"Failed to split audio into chunks:\n{str(e)}"
        ) from e


# ============================================================
# MAIN INPUT PROCESSOR
# ============================================================

def process_input(source: str) -> list:
    """
    Process either:

        1. YouTube URL
        2. Local audio/video file

    Returns:
        List of WAV audio chunk paths.
    """

    if not source:

        raise ValueError(
            "Please provide a YouTube URL "
            "or local audio/video file."
        )

    source = source.strip()

    # ========================================================
    # YouTube
    # ========================================================

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL."
        )

        wav_path = download_youtube_audio(
            source
        )

    # ========================================================
    # Local file
    # ========================================================

    else:

        print(
            "Detected local audio/video file."
        )

        wav_path = convert_to_wav(
            source
        )

    # ========================================================
    # Chunk audio
    # ========================================================

    print(
        "Preparing audio chunks..."
    )

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=10
    )

    if not chunks:

        raise RuntimeError(
            "No audio chunks were created."
        )

    print(
        f"Audio processing completed. "
        f"{len(chunks)} chunk(s) ready."
    )

    return chunks