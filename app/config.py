import os
from pathlib import Path

DATA_DIR = Path(os.getenv("LEGAL_AI_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration - Support for free APIs
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()  # groq, gemini, or anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
