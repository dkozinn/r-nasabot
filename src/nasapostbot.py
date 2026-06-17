#!/usr/bin/python3
"""Bot to send new post titles to Discord"""

import logging
import sys
import time

import praw
from prawcore.exceptions import ServerError, ResponseException
from discord_webhook import DiscordWebhook

from nasautils.utilities import get_sub
from nasautils.utilities import notify

SUB = get_sub()
MAX_AGE = 3600 * 24  # 24 hours to allow for modqueue


def main():
    """Main loop"""

    reddit = praw.Reddit(
        "nasapostbot", user_agent="r-nasapostbot:v1.00 (by /u/dkozinn)"
    )
    app_debug_level = reddit.config.custom["app_debugging"].upper()  # type: ignore
    praw_debug_level = reddit.config.custom["praw_debugging"].upper()  # type: ignore
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
    logging.info("Entering main loop for r/%s", SUB)
    for submission in subreddit.stream.submissions(skip_existing=True):
        reddit_url = "https://reddit.com" + submission.permalink
        if time.time() - submission.created_utc > MAX_AGE:
            logging.warning(
                "Old post ignored: '%s' from %s at %s created on %s",
                submission.title,
                submission.author,
                reddit_url,
                time.ctime(submission.created_utc),
            )
        else:
            logging.info(
                "New post in r/%s by %s: %s (%s)",
                SUB,
                submission.author,
                submission.title,
                reddit_url,
            )
            try:
                webhook = DiscordWebhook(
                    url=discord_webhook,  # type: ignore
                    rate_limit_retry=True,
                    username=f"{SUB} Post Bot",
                    content=(
                        f"[{submission.title}]({reddit_url})"
                        f" by [{submission.author.name}](<https://reddit.com/u/{submission.author.name}>)"
                    ),
                )
                webhook.execute()
            except Exception as e:  # pylint: disable=broad-except
                logging.exception("Error sending to Discord: %s", str(e))


def cli_main() -> None:
    """Entry point for console / systemd; handles process exit and notifications."""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except (ServerError, ResponseException):
        logging.exception("Reddit error")
        sys.exit(2)
    except Exception as error:  # pylint: disable=broad-except
        logging.exception("Unexpected error")
        notify(str(error), title="nasapostbot crashed", priority=1)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
