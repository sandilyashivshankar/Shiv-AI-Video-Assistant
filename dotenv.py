"""Small deployment-safe fallback for load_dotenv.

The Streamlit app imports ``load_dotenv``. This local module keeps the app
working even if python-dotenv is unavailable during a deployment, while also
copying Streamlit secrets into environment variables used by the project.
"""

import os
from pathlib import Path


def _load_env_file() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _load_streamlit_secrets() -> None:
    try:
        import streamlit as st
        secrets = st.secrets
    except Exception:
        return

    for key in ("MISTRAL_API_KEY", "SARVAM_API_KEY", "WHISPER_MODEL", "WISPER_MODEL", "SARVAM_STT_MODEL"):
        try:
            value = secrets.get(key)
        except Exception:
            value = None
        if value and key not in os.environ:
            os.environ[key] = str(value)

    # Keep compatibility with the project's historical WISPER_MODEL spelling.
    if os.getenv("WISPER_MODEL") and not os.getenv("WHISPER_MODEL"):
        os.environ["WHISPER_MODEL"] = os.environ["WISPER_MODEL"]


def load_dotenv(*args, **kwargs) -> bool:
    _load_env_file()
    _load_streamlit_secrets()
    return True
