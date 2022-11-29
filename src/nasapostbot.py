#!/usr/bin/python3
"""Bot to send new post titles to Discord"""

import logging
import sys
from os import system

import praw
import prawcore
from discord_webhook import DiscordWebhook


SUB = "nasa"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasapostbot")
    app_debug_level = reddit.config.custom["app_debugging"].upper()
    praw_debug_level = reddit.config.custom["praw_debugging"].upper()
    discord_webhook = reddit.config.custom["discord_webhook"]
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
    for submission in subreddit.stream.submissions(skip_existing=True):
        reddit_url = "https://reddit.com" + submission.permalink
        logging.info(
            "New post by %s: %s (%s)", submission.author, submission.title, reddit_url
        )
        webhook = DiscordWebhook(
            discord_webhook,
            username="nasapostbot",
            content=f"[{submission.title}]({reddit_url})",
        )
        webhook.execute()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except prawcore.exceptions.ServerError:
        logging.exception("Reddit error")
        sys.exit(2)
    except Exception as error:  # pylint: disable=broad-except
        logging.exception("Unexpected error")
        system("ntfy -o priority 1 -t 'nasapostbot crashed' send '" + str(error) + "'")
        sys.exit(1)
