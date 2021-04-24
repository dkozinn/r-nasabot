#!/usr/bin/python3
"""Bot to send new items in modqueue to Discord"""

import logging
from os import system
import sys

import praw

from nasautils.discord_alert import discord_alert

SUB = "nasa"
#MODQUEUE_URL = f"https://www.reddit.com/r/{SUB}/about/modqueue/"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasamodqbot")
    app_debug_level = reddit.config.custom['app_debugging'].upper()
    praw_debug_level = reddit.config.custom['praw_debugging'].upper()
    discord_webhook = reddit.config.custom["discord_webhook"]

    logging.basicConfig(level=app_debug_level,
                        format="%(levelname)s - %(module)s:%(funcName)s:%(lineno)d — %(message)s",
                        datefmt="%c")
    handler = logging.StreamHandler()
    handler.setLevel(praw_debug_level)
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(praw_debug_level)
        logger.addHandler(handler)

    subreddit = reddit.subreddit(SUB)
    logging.info("Entering main loop")

    for submission in subreddit.mod.stream.modqueue():
        title = getattr(submission, "title", "Comment")
        link = f"https://reddit.com{submission.permalink}"
        logging.debug("New modqueue entry from %s: %s (%s)",
                      submission.author, title, link)
        discord_alert(discord_webhook, "NASA Modqueue Bot",
                      f"Modqueue: {title} by {submission.author}", link)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:
        logging.exception("Unexpected error")
        system(
            "ntfy -o priority 1 -t 'nasa modqueue bot crashed' send '" + str(error) + "'")
        sys.exit(1)
