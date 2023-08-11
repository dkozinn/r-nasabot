#!/usr/bin/python3

"""Bot to send new items in modqueue to Discord"""

import logging
import logging.handlers

import sys
from os import system

import praw
import prawcore
from discord_webhook import DiscordWebhook

try:
    from q_signals import Q_WHITE, send_signal  # type: ignore

    GOT_Q = True
except ModuleNotFoundError:
    GOT_Q = False

SUB = "nasa"


def main():
    """Main loop"""

    reddit = praw.Reddit("nasamodqbot")
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

# Debug rate limiting

    handler = logging.handlers.RotatingFileHandler('/var/log/debug/nasamodqbot-prawcore_log.txt', maxBytes=1024*1024*16, backupCount=5)
    logger = logging.getLogger("prawcore")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    subreddit = reddit.subreddit(SUB)
    logging.info("Entering main loop")

    for submission in subreddit.mod.stream.modqueue():
        try:
            title = getattr(submission, "title")
        except AttributeError:  # If no title, then we have a comment
            title = f"Comment on post '{submission.link_title}'"
        link = f"https://reddit.com{submission.permalink}"
        logging.info(
            "New modqueue entry from %s: %s (%s)", submission.author, title, link
        )
        webhook = DiscordWebhook(
            discord_webhook,
            username="NASA Modqueue Bot",
            content=f"Modqueue: [{title} by {submission.author}]({link})",
        )
        webhook.execute()

        if GOT_Q:
            send_signal(
                Q_WHITE,
                f"Modqueue: {title} by {submission.author}",
                name="Modqueue post",
            )


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
        system(
            "ntfy -o priority 1 -t 'nasa modqueue bot crashed' send '"
            + str(error)
            + "'"
        )
        sys.exit(1)
