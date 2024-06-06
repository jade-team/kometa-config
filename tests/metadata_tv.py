import logging
import yaml
import os

url_poster_base = (
    "https://github.com/jade-team/kometa-config/raw/main/metadata/tv/assets/"
)
file_dir = os.path.dirname(os.path.realpath("__file__"))


class CallCounted:
    def __init__(self, method):
        self.method = method
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self.method(*args, **kwargs)


def run() -> int:
    logging.info("=" * 50)
    logging.error = CallCounted(logging.error)

    with open(os.path.join(file_dir, "./metadata/tv/tv.yml"), "r") as file:
        prime_service = yaml.safe_load(file)
        assets = os.listdir(os.path.join(file_dir, "./metadata/tv/assets"))
        total_seasons = sum(
            len(tv_data.get("seasons", {}))
            for tv_data in prime_service["metadata"].values()
        )

        logging.info(
            f"Testing Metadata - TV Shows over {len(prime_service['metadata'])} tv shows, {total_seasons} seasons and {len(assets)} assets"
        )

        for tv_id, tv_data in prime_service["metadata"].items():
            if not tv_data:
                logging.error(f"TV Show {tv_id} fields are missing")
            else:
                title = tv_data.get("title", None)
                url_poster = tv_data.get("url_poster", None)
                seasons = tv_data.get("seasons", None)

                if not title:
                    logging.error(f"TV Show {tv_id} title field is missing")
                if not url_poster:
                    logging.error(
                        f"TV Show {tv_id} - {title} url_poster field is missing"
                    )
                if url_poster:
                    if not url_poster.startswith(url_poster_base):
                        logging.error(
                            f"TV Show {tv_id} - {title} has an invalid url_poster base uri"
                        )
                    poster_file = url_poster[len(url_poster_base) :]
                    if not poster_file.startswith(str(tv_id)):
                        logging.error(
                            f"TV Show {tv_id} - {title} has a different TMDB Id and url_poster TMDB Id ({poster_file})"
                        )
                    if not url_poster.endswith(".jpg"):
                        logging.error(
                            f"TV Show {tv_id} - {title} has an invalid url_poster extension (.jpg)"
                        )
                    if not poster_file in assets:
                        logging.error(
                            f"TV Show {tv_id} - {title} url_poster ({poster_file}) NOT found in assets folder"
                        )
                    else:
                        assets.remove(poster_file)

                if seasons:
                    for season_id, season_data in seasons.items():
                        url_poster = season_data.get("url_poster", None)
                        if url_poster:
                            if not url_poster.startswith(url_poster_base):
                                logging.error(
                                    f"TV Show {tv_id} - S{season_id} - {title} has an invalid url_poster base uri"
                                )
                            poster_file = url_poster[len(url_poster_base) :]
                            if not poster_file.startswith(str(tv_id)):
                                logging.error(
                                    f"TV Show {tv_id} - S{season_id} - {title} has a different TMDB Id and url_poster TMDB Id ({poster_file})"
                                )
                            if not url_poster.endswith(".jpg"):
                                logging.error(
                                    f"TV Show {tv_id} - S{season_id} - {title} has an invalid url_poster extension (.jpg)"
                                )
                            if not poster_file in assets:
                                logging.error(
                                    f"TV Show {tv_id} - {title} url_poster ({poster_file}) NOT found in assets folder"
                                )
                            else:
                                assets.remove(poster_file)

        if assets:
            for asset in assets:
                logging.error(f"{asset} file in assets folder is NOT used")

        logging.info(f"{logging.error.counter} Error/s found")

        return logging.error.counter
