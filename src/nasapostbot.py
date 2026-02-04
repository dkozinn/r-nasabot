#!/usr/bin/python3
"""Bot to send new post titles to Discord"""

import logging
import sys
import time
from os import system

import praw
import prawcore
from discord_webhook import DiscordWebhook

from nasautils.utilities import get_sub
from test_praw_debug import PRAWDebugger


SUB = get_sub()
MAX_AGE = 3600 * 24  # 24 hours to allow for modqueue


def main():
    """Main loop"""

    try:
        debugger = PRAWDebugger(praw.Reddit("nasapostbot"), cassette_dir=f"/big/{SUB}")
        reddit = debugger.reddit

        # reddit = praw.Reddit("nasapostbot", user_agent="r-nasapostbot:v1.00 (by /u/dkozinn)",
        #                      requestor_class=request_debug.JSONDebugRequestor)
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
        logging.info("Entering main loop for r/%s", SUB)
        for submission in debugger.stream(
            subreddit.stream.submissions(skip_existing=True)
        ):
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
                    "New post in r/%s by %s: %s (%s)", SUB, submission.author, submission.title, reddit_url
                )
                try:
                    webhook = DiscordWebhook(
                        url=discord_webhook,
                        rate_limit_retry=True,
                        username=f"{SUB} Post Bot",
                        content=(
                            f"[{submission.title}]({reddit_url})"
                            f" by [{submission.author.name}](<https://reddit.com/u/{submission.author.name}>)"
                        )
                    )
                    webhook.execute()
                except Exception as e:  # pylint: disable=broad-except
                    logging.exception("Error sending to Discord: %s", str(e))

    except KeyboardInterrupt:
        debugger.stop()
        sys.exit(0)
    except Exception as error: #pylint: disable=broad-except
        debugger.stop()
        print(error)
        sys.exit(0)




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except (prawcore.exceptions.ServerError, prawcore.exceptions.ResponseException):
        logging.exception("Reddit error")
        sys.exit(2)
    except Exception as error:  # pylint: disable=broad-except
        logging.exception("Unexpected error")
        # system("ntfy -o priority 1 -t 'nasapostbot crashed' send '" + str(error) + "'")
        print(error)
        sys.exit(1)
