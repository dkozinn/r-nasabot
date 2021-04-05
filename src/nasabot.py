#!/usr/bin/python3
"""Bot to flag posts that have hit /r/all on Reddit"""

import logging
#import requests

import praw

from nasautils.discord_alert import discord_alert

SUB = "nasa"
REPLY_TEMPLATE = ("If you're visiting here perhaps for the first time from /r/all, "
                  "welcome to /r/nasa! Please take a moment to "
                  "[read our welcome post](https://www.reddit.com/r/nasa/comments/l43hoq/welcome_to_rnasa_please_read_this_post_for/)"
                  " before posting, and we hope you'll stick around for a while.")
FLAIR_TEMPLATE_ID = "7216c708-7c40-11e4-b13d-12313d052165"
# FLAIR_TEMPLATE_ID="b37f60b8-74ac-11eb-9178-0e509773c193" #TOY
DISCORD_MOD_ID = ""
DISCORD_WEBHOOK = ""


def main():
    """Main loop"""

    global DISCORD_MOD_ID, DISCORD_WEBHOOK
    reddit = praw.Reddit("nasabot")
    DISCORD_WEBHOOK = reddit.config.custom["discord_webhook"]
    DISCORD_MOD_ID = reddit.config.custom["discord_mod_id"]
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

# Iterate through submissions, process if it's the right subreddit and
# it either has no flair or it has flair not matching the template

    for submission in reddit.subreddit('all').hot(limit=250):
        logging.debug("Post in /r/"+str(submission.subreddit) +
                      ":"+submission.title+"/"+submission.id)
        if submission.subreddit == SUB:
            if submission.link_flair_text != "/r/all":      # If flair doesn't say /r/all, process
                process_submission(submission)
            # If flair is /r/all but wrong template, process
            elif getattr(submission, 'link_flair_template_id', "NONE") != FLAIR_TEMPLATE_ID:
                process_submission(submission)


def process_submission(submission):
    """Process a submission by replying, distinguishing the reply, and flairing"""

    logging.info("Replying in /r/"+str(submission.subreddit)+":" +
                 submission.title+"/"+str(submission.author)+"/"+submission.id)
    try:
        comment = submission.reply(REPLY_TEMPLATE)
        comment.mod.distinguish(how="yes", sticky=True)
        submission.mod.flair(
            flair_template_id=FLAIR_TEMPLATE_ID, text="/r/all")
        discord_alert(
            DISCORD_WEBHOOK, "nasabot",
            f"{DISCORD_MOD_ID} Submission titled '{submission.title}' at https://reddit.com/r/{SUB}{submission.permalink} has hit /r/all")
    except praw.exceptions.PRAWException as error:
        logging.warning("Exception \"%s\" for id %s with title %s",
                        error, submission.id, submission.title)


if __name__ == "__main__":
    main()
