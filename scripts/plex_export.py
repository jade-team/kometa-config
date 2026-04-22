#!/usr/bin/env python3
"""
Plex Export
===========
Exports movies and TV shows from Plex to CSV files with configurable filters.

Usage: python scripts/plex_export.py
Configuration: Edit config.py to set your Plex server URL and token.
Requirements: pip install plexapi
"""

import csv
import sys
from pathlib import Path
from typing import List, Dict
from plexapi.server import PlexServer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from config import PLEX_URL, PLEX_TOKEN, MOVIES_CSV, SHOWS_CSV

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = PROJECT_ROOT / "_output"


def is_poster_locked(item) -> bool:
    """
    Check if the poster (thumb) is locked for a Plex item.

    Args:
        item: A Plex media item (movie, show, etc.)

    Returns:
        True if poster is locked, False otherwise
    """
    try:
        # fields is a list of Field objects
        for field in item.fields:
            if field.name == "thumb" and hasattr(field, "locked"):
                return field.locked
        # If no thumb field found or no locked attribute, assume unlocked
        return False
    except:
        # If any error, assume unlocked
        return False


def get_tmdb_id(item) -> str:
    """
    Extract TMDB ID from a Plex item.

    Args:
        item: A Plex media item (movie, show, etc.)

    Returns:
        TMDB ID as string, or empty string if not found
    """
    try:
        if hasattr(item, "guids"):
            for guid in item.guids:
                if hasattr(guid, "id") and "tmdb://" in guid.id:
                    return guid.id.replace("tmdb://", "")
        return ""
    except:
        return ""


def get_unlocked_movies(plex: PlexServer) -> List[Dict]:
    """
    Get all movies whose poster is not locked.

    Returns:
        List of dictionaries with movie information
    """
    print("🎬 Scanning movies...")
    unlocked_movies = []

    try:
        # Get all movie libraries
        for section in plex.library.sections():
            if section.type == "movie":
                print(f"  📁 Processing library: {section.title}")
                movies = section.all()

                for movie in movies:
                    # Check if poster is not locked
                    if not is_poster_locked(movie):
                        movie_data = {
                            "type": "movie",
                            "title": movie.title,
                            "year": movie.year if hasattr(movie, "year") else "",
                            "tmdb_id": get_tmdb_id(movie),
                            "rating": movie.rating if hasattr(movie, "rating") else "",
                            "duration": f"{movie.duration // 60000} min"
                            if hasattr(movie, "duration") and movie.duration
                            else "",
                            "added_at": movie.addedAt.strftime("%Y-%m-%d %H:%M:%S")
                            if hasattr(movie, "addedAt")
                            else "",
                            "library": section.title,
                            "key": movie.key,
                            "poster_locked": "No",
                        }
                        unlocked_movies.append(movie_data)

                print(
                    f"    ✓ Found {len([m for m in unlocked_movies if m['library'] == section.title])} movies with unlocked posters"
                )

    except Exception as e:
        print(f"❌ Error scanning movies: {e}")
        sys.exit(1)

    return unlocked_movies


def get_unlocked_shows(plex: PlexServer) -> List[Dict]:
    """
    Get all TV shows whose poster is not locked.

    Returns:
        List of dictionaries with show information
    """
    print("\n📺 Scanning TV shows...")
    unlocked_shows = []

    try:
        # Get all TV show libraries
        for section in plex.library.sections():
            if section.type == "show":
                print(f"  📁 Processing library: {section.title}")
                shows = section.all()

                for show in shows:
                    # Check if poster is not locked
                    if not is_poster_locked(show):
                        show_data = {
                            "type": "show",
                            "title": show.title,
                            "year": show.year if hasattr(show, "year") else "",
                            "tmdb_id": get_tmdb_id(show),
                            "rating": show.rating if hasattr(show, "rating") else "",
                            "seasons": show.childCount
                            if hasattr(show, "childCount")
                            else "",
                            "episodes": show.leafCount
                            if hasattr(show, "leafCount")
                            else "",
                            "added_at": show.addedAt.strftime("%Y-%m-%d %H:%M:%S")
                            if hasattr(show, "addedAt")
                            else "",
                            "library": section.title,
                            "key": show.key,
                            "poster_locked": "No",
                        }
                        unlocked_shows.append(show_data)

                print(
                    f"    ✓ Found {len([s for s in unlocked_shows if s['library'] == section.title])} shows with unlocked posters"
                )

    except Exception as e:
        print(f"❌ Error scanning TV shows: {e}")
        sys.exit(1)

    return unlocked_shows


def export_to_csv(data: List[Dict], filename: str, fieldnames: List[str]):
    """Export data to CSV file."""
    if not data:
        print(f"⚠️  No data to export to {filename}")
        return

    try:
        # Ensure output directory exists
        OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

        # Write to output directory
        output_file = OUTPUT_PATH / filename
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Exported {len(data)} items to {output_file}")

    except Exception as e:
        print(f"❌ Error exporting to {filename}: {e}")
        sys.exit(1)


def main():
    """Main execution function."""
    print("=" * 70)
    print("Plex Export")
    print("=" * 70)

    # Check configuration
    if not PLEX_TOKEN:
        print("\n❌ Error: PLEX_TOKEN is not set!")
        print("\nPlease update the PLEX_TOKEN in config.py")
        print("\nTo get your Plex token:")
        print("1. Open Plex Web App")
        print("2. Play any item")
        print("3. Click the three dots (...) > Get Info")
        print("4. Click 'View XML'")
        print("5. Look for 'X-Plex-Token' in the URL")
        print(
            "\nOr visit: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/"
        )
        sys.exit(1)

    # Connect to Plex server
    print(f"\n🔌 Connecting to Plex server at {PLEX_URL}...")
    try:
        plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        print(f"✅ Connected to: {plex.friendlyName}")
    except Exception as e:
        print(f"❌ Failed to connect to Plex server: {e}")
        sys.exit(1)

    # Get unlocked movies
    movies = get_unlocked_movies(plex)

    # Get unlocked TV shows
    shows = get_unlocked_shows(plex)

    # Export to CSV
    print("\n📝 Exporting data to CSV files...")

    if movies:
        movie_fields = [
            "type",
            "title",
            "year",
            "tmdb_id",
            "rating",
            "duration",
            "added_at",
            "library",
            "key",
            "poster_locked",
        ]
        export_to_csv(movies, MOVIES_CSV, movie_fields)

    if shows:
        show_fields = [
            "type",
            "title",
            "year",
            "tmdb_id",
            "rating",
            "seasons",
            "episodes",
            "added_at",
            "library",
            "key",
            "poster_locked",
        ]
        export_to_csv(shows, SHOWS_CSV, show_fields)

    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print(f"  Movies with unlocked posters: {len(movies)}")
    print(f"  TV Shows with unlocked posters: {len(shows)}")
    print("=" * 70)
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
