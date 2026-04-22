#!/usr/bin/env python3
"""
Generate Assets from TMDB
==========================
Reads a CSV with TMDB IDs and generates Kometa-compatible assets and YAML files.

Usage: python scripts/generate_assets_from_tmdb.py <csv_file>
Configuration: Edit .env to set your TMDB API key.
Requirements: pip install requests pyyaml python-dotenv
"""

import argparse
import csv
import os
import sys
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from config import (
    TMDB_API_KEY,
    TMDB_API_BASE_URL,
    TMDB_IMAGE_BASE_URL,
    GITHUB_REPO_BASE_URL,
)

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
METADATA_PATH = PROJECT_ROOT / "metadata"


# ──────────────────────────────────────────────────────────────────────────────
# Configuration Constants
# ──────────────────────────────────────────────────────────────────────────────
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 0.25  # seconds
MAX_RETRY_DELAY = 10.0  # seconds
REQUEST_DELAY = 0.02  # 20ms between requests (50 req/s limit)


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified text
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def ensure_directory(path: Path) -> None:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path to create
    """
    path.mkdir(parents=True, exist_ok=True)


def make_api_request(
    url: str, params: Dict = None, retry_count: int = 0
) -> Optional[Dict]:
    """
    Make an API request with retry logic and exponential backoff.

    Args:
        url: API endpoint URL
        params: Query parameters
        retry_count: Current retry attempt

    Returns:
        JSON response or None if failed
    """
    try:
        time.sleep(REQUEST_DELAY)  # Rate limiting
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limited
            if retry_count < MAX_RETRIES:
                delay = min(INITIAL_RETRY_DELAY * (2**retry_count), MAX_RETRY_DELAY)
                print(
                    f"  ⚠️  Rate limited. Waiting {delay:.2f}s before retry {retry_count + 1}/{MAX_RETRIES}..."
                )
                time.sleep(delay)
                return make_api_request(url, params, retry_count + 1)
            else:
                print(f"  ❌ Max retries reached for {url}")
                return None
        else:
            print(f"  ❌ API request failed with status {response.status_code}: {url}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request error: {e}")
        if retry_count < MAX_RETRIES:
            delay = min(INITIAL_RETRY_DELAY * (2**retry_count), MAX_RETRY_DELAY)
            time.sleep(delay)
            return make_api_request(url, params, retry_count + 1)
        return None


def download_image(url: str, output_path: Path, retry_count: int = 0) -> bool:
    """
    Download an image from URL to file.

    Args:
        url: Image URL
        output_path: Output file path
        retry_count: Current retry attempt

    Returns:
        True if successful, False otherwise
    """
    try:
        time.sleep(REQUEST_DELAY)  # Rate limiting
        response = requests.get(url, timeout=30, stream=True)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        elif response.status_code == 429:  # Rate limited
            if retry_count < MAX_RETRIES:
                delay = min(INITIAL_RETRY_DELAY * (2**retry_count), MAX_RETRY_DELAY)
                print(f"  ⚠️  Rate limited. Waiting {delay:.2f}s before retry...")
                time.sleep(delay)
                return download_image(url, output_path, retry_count + 1)

        print(f"  ❌ Failed to download image: {response.status_code}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Download error: {e}")
        if retry_count < MAX_RETRIES:
            delay = min(INITIAL_RETRY_DELAY * (2**retry_count), MAX_RETRY_DELAY)
            time.sleep(delay)
            return download_image(url, output_path, retry_count + 1)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# TMDB API Functions
# ──────────────────────────────────────────────────────────────────────────────


def get_movie_details(tmdb_id: str) -> Optional[Dict]:
    """
    Get movie details from TMDB API.

    Args:
        tmdb_id: TMDB movie ID

    Returns:
        Movie details dictionary or None
    """
    url = f"{TMDB_API_BASE_URL}/movie/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "es-ES"}
    return make_api_request(url, params)


def get_tv_details(tmdb_id: str) -> Optional[Dict]:
    """
    Get TV show details from TMDB API.

    Args:
        tmdb_id: TMDB TV show ID

    Returns:
        TV show details dictionary or None
    """
    url = f"{TMDB_API_BASE_URL}/tv/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "es-ES"}
    return make_api_request(url, params)


def get_movie_images(tmdb_id: str, original_language: str = "en") -> Optional[Dict]:
    """
    Get available images for a movie.

    Args:
        tmdb_id: TMDB movie ID
        original_language: Original language of the movie

    Returns:
        Images data or None
    """
    url = f"{TMDB_API_BASE_URL}/movie/{tmdb_id}/images"
    # Include Spanish variants and original language
    languages = f"es,es-ES,es-MX,{original_language},null"
    params = {"api_key": TMDB_API_KEY, "include_image_language": languages}
    return make_api_request(url, params)


def get_tv_images(tmdb_id: str, original_language: str = "en") -> Optional[Dict]:
    """
    Get available images for a TV show.

    Args:
        tmdb_id: TMDB TV show ID
        original_language: Original language of the show

    Returns:
        Images data or None
    """
    url = f"{TMDB_API_BASE_URL}/tv/{tmdb_id}/images"
    # Include Spanish variants and original language
    languages = f"es,es-ES,es-MX,{original_language},null"
    params = {"api_key": TMDB_API_KEY, "include_image_language": languages}
    return make_api_request(url, params)


def get_primary_poster(
    images_data: Dict, preferred_lang: str = "es-ES"
) -> Optional[str]:
    """
    Get the primary poster path from images data.

    Args:
        images_data: Images data from TMDB API
        preferred_lang: Preferred language for poster

    Returns:
        Poster file path or None
    """
    if not images_data or "posters" not in images_data:
        return None

    posters = images_data["posters"]
    if not posters:
        return None

    # Try to find poster in preferred language
    for poster in posters:
        if poster.get("iso_639_1") == preferred_lang.split("-")[0]:
            return poster["file_path"]

    # Fallback to first available poster
    return posters[0]["file_path"]


def get_alternative_posters(images_data: Dict, original_language: str) -> List[Dict]:
    """
    Get alternative posters in es-ES, es-MX, and original language.

    Args:
        images_data: Images data from TMDB API
        original_language: Original language of the media

    Returns:
        List of poster dictionaries with file_path and language
    """
    if not images_data or "posters" not in images_data:
        return []

    # Target Spanish variants and original language
    target_languages = {"es", original_language}
    posters = []

    for poster in images_data["posters"]:
        lang = poster.get("iso_639_1")
        # Include posters in target languages or without language (None/null)
        if lang in target_languages or lang is None:
            # Label None as 'no-lang' instead of 'original'
            lang_label = lang if lang else "no-lang"
            posters.append(
                {
                    "file_path": poster["file_path"],
                    "language": lang_label,
                    "vote_average": poster.get("vote_average", 0),
                }
            )

    return posters


# ──────────────────────────────────────────────────────────────────────────────
# Asset Generation Functions
# ──────────────────────────────────────────────────────────────────────────────


def generate_identifier(tmdb_id: str, title: str) -> str:
    """
    Generate identifier in format: tmdb_id-slug.

    Args:
        tmdb_id: TMDB ID
        title: Title to slugify

    Returns:
        Formatted identifier
    """
    return f"{tmdb_id}-{slugify(title)}"


def process_movie(tmdb_id: str, base_path: Path) -> Optional[Dict]:
    """
    Process a single movie: fetch data, download assets, prepare YAML entry.

    Args:
        tmdb_id: TMDB movie ID
        base_path: Base path for output

    Returns:
        Dictionary with YAML entry data or None if failed
    """
    print(f"  🎬 Processing movie {tmdb_id}...")

    # Get movie details
    details = get_movie_details(tmdb_id)
    if not details:
        print("    ❌ Failed to get movie details")
        return None

    title = details.get("title", "")
    original_language = details.get("original_language", "en")
    identifier = generate_identifier(tmdb_id, details.get("original_title", title))

    # Get images (include original language)
    images = get_movie_images(tmdb_id, original_language)
    if not images:
        print("    ⚠️  No images found for movie")
        return None

    # Download primary poster
    primary_poster_path = get_primary_poster(images, "es-ES")
    if primary_poster_path:
        assets_dir = base_path / "movies" / "assets"
        ensure_directory(assets_dir)

        poster_filename = f"{identifier}.jpg"
        poster_url = f"{TMDB_IMAGE_BASE_URL}/original{primary_poster_path}"

        if download_image(poster_url, assets_dir / poster_filename):
            print(f"    ✅ Downloaded primary poster: {poster_filename}")
        else:
            print("    ❌ Failed to download primary poster")

    # Download alternative posters
    alt_posters = get_alternative_posters(images, original_language)
    if alt_posters:
        alt_dir = base_path / "movies_alt" / identifier
        ensure_directory(alt_dir)

        for idx, poster in enumerate(alt_posters):
            filename = f"poster_{idx + 1}_{poster['language']}.jpg"
            poster_url = f"{TMDB_IMAGE_BASE_URL}/original{poster['file_path']}"

            if download_image(poster_url, alt_dir / filename):
                print(f"    ✅ Downloaded alt poster: {filename}")

    # Prepare YAML entry
    url_poster = f"{GITHUB_REPO_BASE_URL}/movies/assets/{identifier}.jpg"

    return {"tmdb_id": int(tmdb_id), "title": title, "url_poster": url_poster}


def process_tv_show(tmdb_id: str, base_path: Path) -> Optional[Dict]:
    """
    Process a single TV show: fetch data, download assets, prepare YAML entry.

    Args:
        tmdb_id: TMDB TV show ID
        base_path: Base path for output

    Returns:
        Dictionary with YAML entry data or None if failed
    """
    print(f"  📺 Processing TV show {tmdb_id}...")

    # Get TV show details
    details = get_tv_details(tmdb_id)
    if not details:
        print("    ❌ Failed to get TV show details")
        return None

    title = details.get("name", "")
    original_language = details.get("original_language", "en")
    identifier = generate_identifier(tmdb_id, details.get("original_name", title))

    # Get images (include original language)
    images = get_tv_images(tmdb_id, original_language)
    if not images:
        print("    ⚠️  No images found for TV show")
        return None

    # Download primary poster
    primary_poster_path = get_primary_poster(images, "es-ES")
    if primary_poster_path:
        assets_dir = base_path / "tv" / "assets"
        ensure_directory(assets_dir)

        poster_filename = f"{identifier}.jpg"
        poster_url = f"{TMDB_IMAGE_BASE_URL}/original{primary_poster_path}"

        if download_image(poster_url, assets_dir / poster_filename):
            print(f"    ✅ Downloaded primary poster: {poster_filename}")
        else:
            print("    ❌ Failed to download primary poster")

    # Download alternative posters
    alt_posters = get_alternative_posters(images, original_language)
    if alt_posters:
        alt_dir = base_path / "tv_alt" / identifier
        ensure_directory(alt_dir)

        for idx, poster in enumerate(alt_posters):
            filename = f"poster_{idx + 1}_{poster['language']}.jpg"
            poster_url = f"{TMDB_IMAGE_BASE_URL}/original{poster['file_path']}"

            if download_image(poster_url, alt_dir / filename):
                print(f"    ✅ Downloaded alt poster: {filename}")

    # Prepare YAML entry
    url_poster = f"{GITHUB_REPO_BASE_URL}/tv/assets/{identifier}.jpg"

    return {"tmdb_id": int(tmdb_id), "title": title, "url_poster": url_poster}


# ──────────────────────────────────────────────────────────────────────────────
# YAML Generation Functions
# ──────────────────────────────────────────────────────────────────────────────


def generate_yaml(entries: List[Dict], output_path: Path) -> None:
    """
    Generate or update YAML file with metadata entries sorted by TMDB ID.
    If file exists, merge new entries with existing ones.

    Args:
        entries: List of entry dictionaries
        output_path: Output YAML file path
    """
    # Build metadata structure from new entries
    metadata = {}

    # Load existing YAML file if it exists
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f)
                if existing_data and "metadata" in existing_data:
                    metadata = existing_data["metadata"]
                    print(
                        f"  📖 Loaded {len(metadata)} existing entries from {output_path.name}"
                    )
        except Exception as e:
            print(f"  ⚠️  Could not load existing YAML, creating new file: {e}")
            metadata = {}

    # Add or update entries (new entries override existing ones with same ID)
    new_count = 0
    updated_count = 0
    for entry in entries:
        tmdb_id = entry["tmdb_id"]
        if tmdb_id in metadata:
            updated_count += 1
        else:
            new_count += 1

        metadata[tmdb_id] = {"title": entry["title"], "url_poster": entry["url_poster"]}

    # Sort by TMDB ID
    sorted_metadata = dict(sorted(metadata.items(), key=lambda x: int(x[0])))

    # Write YAML file
    yaml_data = {"metadata": sorted_metadata}

    ensure_directory(output_path.parent)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.dump(
            yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    print(
        f"✅ Generated YAML: {output_path} ({new_count} new, {updated_count} updated, {len(sorted_metadata)} total)"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main Processing Functions
# ──────────────────────────────────────────────────────────────────────────────


def read_csv(csv_path: str) -> Tuple[List[Dict], int, int]:
    """
    Read CSV file and extract TMDB IDs and types.

    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (valid items list, total rows, skipped rows)
    """
    items = []
    total_rows = 0
    skipped_rows = 0

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                tmdb_id = row.get("tmdb_id", "").strip()
                item_type = row.get("type", "").strip()
                title = row.get("title", "").strip()

                if tmdb_id and item_type:
                    items.append({"tmdb_id": tmdb_id, "type": item_type})
                else:
                    skipped_rows += 1
                    if not tmdb_id:
                        print(f"  ⚠️  Skipping '{title}' - missing tmdb_id")

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)

    return items, total_rows, skipped_rows


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate Kometa assets from TMDB IDs in a CSV file."
    )
    parser.add_argument(
        "csv_file", help="Path to CSV file with tmdb_id and type columns"
    )
    parser.add_argument(
        "-o", "--output", default=None, help="Output directory (default: metadata/)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Generate Assets from TMDB")
    print("=" * 70)

    # Check API key
    if not TMDB_API_KEY:
        print("\n❌ Error: TMDB_API_KEY is not set!")
        print("\n💡 Please check:")
        print("  1. .env file exists in the project root")
        print("  2. python-dotenv is installed: pip install -r requirements.txt")
        print("  3. .env file has the correct format (see .env.template)")
        print("\nGet your TMDB API key from: https://www.themoviedb.org/settings/api")
        sys.exit(1)

    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"\n❌ Error: CSV file not found: {args.csv_file}")
        sys.exit(1)

    # Read CSV
    print(f"\n📄 Reading CSV: {args.csv_file}")
    items, total_rows, skipped_rows = read_csv(args.csv_file)

    print("\n📊 CSV Summary:")
    print(f"   Total rows: {total_rows}")
    print(f"   Valid items (with tmdb_id): {len(items)}")
    print(f"   Skipped items (missing tmdb_id): {skipped_rows}")

    if not items:
        print("\n⚠️  No valid items found in CSV")
        print("\n💡 Tip: Items need a valid 'tmdb_id' to be processed.")
        print("   Make sure your Plex library uses TMDB as the metadata agent.")
        sys.exit(0)

    print(f"\n✅ Processing {len(items)} items...")

    # Count by type
    movies_count = sum(1 for item in items if item["type"] == "movie")
    shows_count = sum(1 for item in items if item["type"] == "show")
    print(f"  🎬 Movies: {movies_count}")
    print(f"  📺 TV Shows: {shows_count}")

    # Determine output path: use provided path or default to metadata/
    if args.output:
        base_path = Path(args.output)
    else:
        base_path = METADATA_PATH
        print(f"\n📁 Output directory: {base_path}")

    # Process items
    movie_entries = []
    tv_entries = []

    print("\n🚀 Processing items...")

    for idx, item in enumerate(items, 1):
        print(f"\n[{idx}/{len(items)}] Processing {item['type']} {item['tmdb_id']}...")

        try:
            if item["type"] == "movie":
                entry = process_movie(item["tmdb_id"], base_path)
                if entry:
                    movie_entries.append(entry)
            elif item["type"] == "show":
                entry = process_tv_show(item["tmdb_id"], base_path)
                if entry:
                    tv_entries.append(entry)
            else:
                print(f"  ⚠️  Unknown type: {item['type']}")

        except Exception as e:
            print(f"  ❌ Error processing item: {e}")
            continue

    # Generate YAML files
    print("\n📝 Generating YAML files...")

    if movie_entries:
        movies_yaml = base_path / "movies" / "movies.yml"
        generate_yaml(movie_entries, movies_yaml)

    if tv_entries:
        tv_yaml = base_path / "tv" / "tv.yml"
        generate_yaml(tv_entries, tv_yaml)

    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"  Movies processed: {len(movie_entries)}/{movies_count}")
    print(f"  TV Shows processed: {len(tv_entries)}/{shows_count}")
    print("=" * 70)
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
