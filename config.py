"""Configuration loader from .env file"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# ──────────────────────────────────────────────────────────────────────────────
# Plex Server Configuration
# ──────────────────────────────────────────────────────────────────────────────
PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")

# ──────────────────────────────────────────────────────────────────────────────
# CSV Output Files Configuration
# ──────────────────────────────────────────────────────────────────────────────
MOVIES_CSV = os.getenv("MOVIES_CSV", "plex_movies_unlocked_posters.csv")
SHOWS_CSV = os.getenv("SHOWS_CSV", "plex_shows_unlocked_posters.csv")

# ──────────────────────────────────────────────────────────────────────────────
# TMDB API Configuration
# ──────────────────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# ──────────────────────────────────────────────────────────────────────────────
# Kometa Configuration
# ──────────────────────────────────────────────────────────────────────────────
GITHUB_REPO_BASE_URL = "https://github.com/jade-team/kometa-config/raw/main/metadata"
