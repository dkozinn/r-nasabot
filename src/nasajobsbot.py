#!/usr/bin/python3
"""Bot to send newly posted NASA Jobs to r/NASAJobs"""

import logging
import sys
from datetime import date

import praw
from prawcore.exceptions import ServerError, ResponseException
from praw.exceptions import RedditAPIException
from requests.exceptions import HTTPError

from nasautils.fetch_jobs import fetch_jobs
from nasautils.utilities import notify

SUB = "nasajobs"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasajobsbot", user_agent="r-nasajobsbot:v1.00 (by /u/dkozinn)")
    app_debug_level = reddit.config.custom["app_debugging"].upper() # type: ignore
    praw_debug_level = reddit.config.custom["praw_debugging"].upper()   # type: ignore
    logging.basicConfig(
        level=app_debug_level,
        filename="/var/log/nasabot.log",
        format="%(asctime)s %(levelname)s - %(module)s:%(funcName)s:%(lineno)d — %(message)s",
        datefmt="%c",
    )
    handler = logging.StreamHandler()
    handler.setLevel(praw_debug_level)
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(praw_debug_level)
        logger.addHandler(handler)

    subreddit = reddit.subreddit(SUB)
    logging.info("Entering main loop")
    results = fetch_jobs(
        reddit.config.custom["jobs_email"], reddit.config.custom["jobs_key"]    #type: ignore
    )
    if len(results) > 0:
        subreddit.submit(
            date.today().strftime("New usajobs.gov NASA postings as of %A %B %-d, %Y"),
            flair_id="c753e058-9ac6-11ee-a880-9a87da1d6157",
            flair_text="usajobs.gov",
            selftext=results,
            send_replies=False,
        )
        logging.info("Posted daily new jobs")
    else:
        logging.info("No jobs found")


def cli_main() -> None:
    """Entry point for console / systemd; handles process exit and notifications."""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except (ServerError, ResponseException):
        logging.exception("Reddit error")
        sys.exit(2)
    except RedditAPIException:
        logging.exception("Reddit API Exception")
    except HTTPError as error:
        logging.exception("HTTPError: %s", error)
        notify(str(error), title="nasajobs HTTPError", priority=0)
        sys.exit(0)
    except Exception as error:  # pylint: disable=broad-except
        logging.exception("Unexpected error")
        notify(str(error), title="nasajobsbot crashed", priority=1)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
