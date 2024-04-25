#!/usr/bin/python3
"""Bot to send newly posted NASA Jobs to r/NASAJobs"""

import logging
import sys
from datetime import date
from os import system

import praw
import prawcore

from nasautils.fetch_jobs import fetch_jobs

SUB = "nasajobs"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasajobsbot")
    app_debug_level = reddit.config.custom["app_debugging"].upper()
    praw_debug_level = reddit.config.custom["praw_debugging"].upper()
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
        reddit.config.custom["jobs_email"], reddit.config.custom["jobs_key"]
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except (prawcore.exceptions.ServerError, prawcore.exceptions.ResponseException):
        logging.exception("Reddit error")
        sys.exit(2)
    except praw.exceptions.RedditAPIException:
        logging.exception("Reddit API Exception")
    except Exception as error:  # pylint: disable=broad-except
        logging.exception("Unexpected error")
        system("ntfy -o priority 1 -t 'nasajobsbot crashed' send '" + str(error) + "'")
        sys.exit(1)
