# Kometa Config

Config files for [Kometa](https://kometa.wiki/) following Spanish versions from [TMDB](https://www.themoviedb.org/).

## Contributing

To facilitate contribution to the repository, we have several scripts that automate common tasks.

### Prerequisites

Before using the scripts, you need to set up your environment:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy the template file: `cp .env.template .env`
   - Edit `.env` and add your credentials:
     - `PLEX_URL`: Your Plex server URL (e.g., `http://192.168.1.100:32400`)
     - `PLEX_TOKEN`: Your Plex authentication token ([how to find it](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/))
     - `TMDB_API_KEY`: Your TMDB API key ([get it here](https://www.themoviedb.org/settings/api))

### Available Scripts

#### 1. Export from Plex

Extracts a CSV list of movies and TV shows from Plex that have unlocked posters. This indicates that Kometa has not yet processed these items.

```bash
python scripts/plex_export.py
```

CSVs are generated in the `_output/` folder:
- `plex_movies_unlocked_posters.csv` (~1337 movies)
- `plex_shows_unlocked_posters.csv` (~347 shows)

#### 2. Process Movies

Processes the previously generated movie CSV (or a custom one) to fetch from TMDB:
- Main metadata for each movie (title, description, etc.) in Spanish (es-ES)
- Main poster in es-ES
- All available posters in original, es-ES, and es-MX languages (for review)

```bash
python scripts/generate_assets_from_tmdb.py _output/plex_movies_unlocked_posters.csv
```

The script automatically updates the metadata YAML files with the new posters and generates:
- Main assets in `metadata/movies/assets/`
- Review assets in separate folders for analysis

#### 3. Process TV Shows

Same as above but for TV shows:

```bash
python scripts/generate_assets_from_tmdb.py _output/plex_shows_unlocked_posters.csv
```

Assets are generated in `metadata/tv/assets/` with the same metadata and review structure.

### CSV Format

The scripts expect a CSV with `tmdb_id` and `type` columns (values: `movie` or `show`). You can create a CSV manually or use the Plex exporter.

## References

For more information about the posters and sets used, see the [references documentation](docs/references.md).
