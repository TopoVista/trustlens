"""Lazy OpenAI client shared by workspace synthesis specialists."""
import os
from typing import Optional
from openai import OpenAI

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")
    if not api_key:
        from dotenv import load_dotenv
        from pathlib import Path
        backend_env = Path(__file__).resolve().parents[2] / ".env"
        root_env = Path(__file__).resolve().parents[3] / ".env"
        for p in [backend_env, root_env]:
            if p.exists():
                load_dotenv(dotenv_path=p, override=True)
        api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is missing. "
            "Please configure OPENAI_API_KEY in backend/.env file."
        )
    if _client is None or getattr(_client, "api_key", None) != api_key:
        _client = OpenAI(api_key=api_key)
    return _client
