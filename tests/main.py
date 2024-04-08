import logging
from metadatamovies import run
from sys import exit

log_level = logging.INFO

if __name__ == "__main__":
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s]\t[%(filename)s]\t[%(levelname)s]\t[%(message)s]",
    )

    errors = run()

    if errors:
        exit(1)
