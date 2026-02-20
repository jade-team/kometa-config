#!/usr/bin/env python3
import re
from pathlib import Path
from ruamel.yaml import YAML

OWNER = "jasimancas"
REPO = "kometa-config"
BRANCH = "main"

ASSETS_DIR = Path("metadata/movies/assets")
YML_PATH = Path("metadata/movies/movies.yml")

RAW_BASE = f"https://github.com/{OWNER}/{REPO}/raw/{BRANCH}/metadata/movies/assets/"

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

IMG_RE = re.compile(r"^(?P<id>\d+)-.+\.(jpg|jpeg|png|webp)$", re.IGNORECASE)


def main():
    if not ASSETS_DIR.exists():
        raise SystemExit(f"No existe la carpeta: {ASSETS_DIR}")

    data = {}
    if YML_PATH.exists():
        data = yaml.load(YML_PATH.read_text(encoding="utf-8")) or {}

    data.setdefault("metadata", {})
    metadata = data["metadata"]

    for img in sorted(ASSETS_DIR.iterdir()):
        if not img.is_file():
            continue

        m = IMG_RE.match(img.name)
        if not m:
            raise SystemExit(f"Nombre inválido: {img.name}. Usa TMDBID-algo.jpg")

        tmdb_id = int(m.group("id"))
        url = RAW_BASE + img.name

        entry = metadata.get(tmdb_id) or {}
        entry["url_poster"] = url
        metadata[tmdb_id] = entry

    with YML_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print("movies.yml actualizado correctamente")


if __name__ == "__main__":
    main()
