#!/usr/bin/python3
"""Bot to send new post titles to Discord"""

import logging
import requests
import sys
from time import sleep

import praw

SUB = "nasa"

def main():
    """Main loop"""

    global discord_mod_id, discord_webhook
    reddit = praw.Reddit("nasapostbot")
    discord_webhook = reddit.config.custom["discord_webhook"]
    discord_mod_id = reddit.config.custom["discord_mod_id"]
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
        reddit_url="https://reddit.com" + submission.permalink
        logging.debug("New post by %s: %s (%s)", submission.author,submission.title,reddit_url)
        discord_alert(reddit_url, submission.title)

def discord_alert(url, title):
    """Send an alert to a Discord channel"""
    
    logging.info("New post: '%s' at %s ", title, url)

    data = {
        "content":" New post: "+url,
        "username": "r-nasapostbot"
    }
    try:
       r=requests.post(discord_webhook, data=data)
       # Always wait at least x-ratelimit-reset-after seconds
       sleep(int(r.headers['X-ratelimit-reset-after']))

       if int(r.headers['X-RateLimit-Remaining']) <= 1:  # We are about to hit the limit, wait a bit more
           logging.warning("Rate limit about to be hit, sleeping %d seconds", int(r.headers['X-ratelimit-reset-after'])*2)
           sleep(int(r.headers['X-ratelimit-reset-after'])*2)
       r.raise_for_status()
    except requests.RequestException as e: #TODO Figure out how to retry the post
        if r.status_code == 429:    # Rate limiting
            retry_after = int(r.headers['retry-after'])/1000    # discord.py/webhook.py does this, not sure why
            logging.warning("Got 429 rate-limit, sleeping for %.2f seconds", retry_after)
            sleep(retry_after)
        else:
            logging.error("Failed to post to discord with error %s", e)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
