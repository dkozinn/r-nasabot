#!/usr/bin/python3
"""Bot to send new post titles to Discord"""

import logging
from os import system
import sys

import praw

from utils import webhook
from utils.discord_alert import discord_alert

SUB = "nasa"

def main():
    """Main loop"""

    reddit = praw.Reddit("nasapostbot")
    app_debug_level = reddit.config.custom['app_debugging'].upper()
    praw_debug_level = reddit.config.custom['praw_debugging'].upper()
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
    for submission in subreddit.stream.submissions(skip_existing=True):
        reddit_url = "https://reddit.com" + submission.permalink
        logging.debug("New post by %s: %s (%s)", submission.author, submission.title, reddit_url)
        discord_alert(webhook, "postbot", reddit_url, submission.title)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:
        system("ntfy -o priority 1 -t 'nasapostbot crashed' send '" + str(error) + "'")
        