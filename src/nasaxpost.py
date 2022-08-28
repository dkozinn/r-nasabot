#!/usr/bin/python3
"""Bot to crosspost all posts from a specified user"""
# pylint enable=useless-suppression
import logging
from os import system
import sys

import prawcore
import praw

SUB = "nasa"
USERSUB = "u_nasa"


def main():
    """Main loop"""

    # Use the same credentials as nasapostbot
    reddit = praw.Reddit("nasapostbot", user_agent="r-nasaxpost:v0.01 (by /u/dkozinn)")
    app_debug_level = reddit.config.custom['app_debugging'].upper()
    praw_debug_level = reddit.config.custom['praw_debugging'].upper()

    logging.basicConfig(level=app_debug_level,
                        filename="/var/log/nasabot.log",
                        format="%(asctime)s %(levelname)s - %(module)s:"
                        "%(funcName)s:%(lineno)d — %(message)s",
                        datefmt="%c")
    handler = logging.StreamHandler()
    handler.setLevel(praw_debug_level)
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(praw_debug_level)
        logger.addHandler(handler)

    subreddit = reddit.subreddit(USERSUB)
    logging.info("Entering main loop")
    for submission in subreddit.stream.submissions(skip_existing=True):
        try:
            cross_post = submission.crosspost(SUB, flair_id="0f2362b2-7fae-11e3-bed4-22000aa47206",
                                              send_replies=False)
        except praw.exceptions.RedditAPIException as exception:
            xpost_error = False
            for subexception in exception.items:
                if subexception.error_type == 'INVALID_CROSSPOST_THING':
                    xpost_error = True
                    break
            if xpost_error:
                logging.warning("Attempt to crosspost http://reddit.com%s failed, skipping",
                                cross_post.permalink)
                continue
            raise

        reddit_url = "https://reddit.com" + cross_post.permalink
        logging.info("Cross-posted '%s' from %s at %s",
                     cross_post.title, cross_post.author, reddit_url)


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
        system("ntfy -o priority 1 -t 'nasaxpost crashed' send '" + str(error) + "'")
        sys.exit(1)
