#!/usr/bin/python3
"""Bot to send new items in modqueue to Discord"""

import logging
from os import system
import sys

import praw

from utils.discord_alert import discord_alert

SUB = "nasa"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasamodqbot")
    app_debug_level = reddit.config.custom['app_debugging'].upper()
    praw_debug_level = reddit.config.custom['praw_debugging'].upper()
    discord_webhook = reddit.config.custom["discord_webhook"]

    logging.basicConfig(level=app_debug_level,
                        format="%(asctime)s — %(levelname)s - %(funcName)s:%(lineno)d — %(message)s",
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
        reddit_url = "https://reddit.com" + submission.permalink
        title = getattr(submission, "title", "Comment")
        logging.debug("New modqueue entry by %s: %s (%s)",
                      submission.author, title, reddit_url)
        discord_alert(discord_webhook, "nasamodqbot",
                      f"New modqueue entry: {title} by {submission.author} {reddit_url}")


if __name__ == "__main__":
    import traceback
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:
        traceback.print_exc()
        logging.fatal(error)
        system("ntfy -o priority 1 -t 'nasa modqueue bot crashed' send '" + str(error) + "'")
