import logging
from metadata_movies import run as run_metadata_movies
from metadata_tv import run as run_metadata_tv
from sys import exit

log_level = logging.INFO

if __name__ == "__main__":
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s]\t[%(filename)s]\t[%(levelname)s]\t[%(message)s]",
    )

    metadata_movies_errors = run_metadata_movies()

    if metadata_movies_errors:
        exit(1)

    metadata_tv_errors = run_metadata_tv()

    if metadata_tv_errors:
        exit(1)
