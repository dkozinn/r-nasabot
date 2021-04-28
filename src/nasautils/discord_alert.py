""" Sends alert to discord about a new reddit post """
import logging
from time import sleep

import requests
from requests.exceptions import HTTPError


def discord_alert(webhook, username, message, url):
    """
    Send an alert to a Discord channel about a new Reddit post

    Parameters:
        webhook: str - webhoook URL
        username: str - Discord username to display
        message: str - message to post
        url: str - Link to post

    """

    # data = {
    #     "content": message,
    #     "username": username
    # }
    data = {
        "embeds": [{
            "title": message,
            "url": url
        }],
        "username": username
    }
    logging.debug("Posting message as %s: %s (%s)", username, message, url)
    try:
        r = requests.post(webhook, json=data)
        r.raise_for_status()

        # Always wait at least x-ratelimit-reset-after seconds
        sleep(int(r.headers['X-ratelimit-reset-after']))

        # If we are about to hit the limit, wait a bit more
        if int(r.headers['X-RateLimit-Remaining']) <= 1:
            logging.warning("Rate limit about to be hit, sleeping %d seconds", int(
                r.headers['X-ratelimit-reset-after'])*2)
            sleep(int(r.headers['X-ratelimit-reset-after'])*2)

    except HTTPError as err:
        if err.response.status_code == 429:  # rate limiting
            # from discord.py/webhook.py
            retry_after = int(r.headers['retry-after'])/1000
            logging.warning(
                "Got 429 rate-limit, sleeping for %.2f seconds", retry_after)
            sleep(retry_after)
        else:
            logging.error("Failed to post to discord with error %s", err)
            raise(err)
