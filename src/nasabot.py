#!/usr/bin/python3

"""Bot to flag posts that have hit /r/all on Reddit"""

import logging
from pathlib import Path

import praw
import praw.exceptions
from discord_webhook import DiscordWebhook

import dbstuff

SUB = "nasa"
DBDIR = str(Path.home())+"/"+SUB
db = dbstuff.NasaDB(DBDIR)


REPLY_TEMPLATE = (
    "If you're visiting here perhaps for the first time from /r/all, "
    "welcome to /r/nasa! Please take a moment to "
    "[read our welcome post]"
    "(https://www.reddit.com/r/nasa/comments/l43hoq/welcome_to_rnasa_please_read_this_post_for/)"
    " before posting, and we hope you'll stick around for a while."
)
FLAIR_TEMPLATE_ID = "7216c708-7c40-11e4-b13d-12313d052165"
# FLAIR_TEMPLATE_ID="b37f60b8-74ac-11eb-9178-0e509773c193" #TOY

reddit = praw.Reddit("nasabot")
DISCORD_WEBHOOK = reddit.config.custom["discord_webhook"]
DISCORD_MOD_ID = reddit.config.custom["discord_mod_id"]
app_debug_level = reddit.config.custom["app_debugging"].upper()
praw_debug_level = reddit.config.custom["praw_debugging"].upper()


def main():

    """Main loop"""

    index = 0
    logging.basicConfig(
        level=app_debug_level,
        filename="/var/log/nasabot.log",
        format="%(asctime)s — %(levelname)s - %(module)s:%(funcName)s:%(lineno)d — %(message)s",
        datefmt="%c",
    )
    handler = logging.StreamHandler()
    handler.setLevel(praw_debug_level)
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(praw_debug_level)
        logger.addHandler(handler)

    # Iterate through submissions, process if it's the right subreddit and
    # it either has no flair or it has flair not matching the template

    for submission in reddit.subreddit("all").hot(limit=250):
        index += 1
        logging.debug(
            "Post in /r/%s:%s/%s index=%s",
            str(submission.subreddit),
            submission.title,
            submission.id,
            str(index),
        )
        if submission.subreddit == SUB:
            oldindex = db.get_rank(submission.id)
            if oldindex is None:    # we haven't seen this submission yet
                process_submission(submission, index)
                db.insert(submission.id,index)
            elif oldindex > index:
                db.update(submission.id,index)
                 print(submission.id,oldindex,index) # TODO: Remove this?
                webhook = DiscordWebhook(
                    DISCORD_WEBHOOK,
                    username="nasabot",
                    content=(
                        f"Updated /r/all index to {index} for "
                        f" '[{submission.title}](http://reddit.com{submission.permalink})'"
                    ),
                )
                webhook.execute()


def process_submission(submission, index):
    """Process a submission by replying, distinguishing the reply, and flairing"""

    logging.info(
        "Post hit /r/all from /r/%s:%s/%s index=%s",
        str(submission.subreddit),
        submission.title,
        str(submission.author),
        str(index),
    )

    try:
        comment = submission.reply(body=REPLY_TEMPLATE)
        comment.mod.distinguish(how="yes", sticky=True)
        comment.disable_inbox_replies()
        submission.mod.flair(flair_template_id=FLAIR_TEMPLATE_ID, text="/r/all")
        webhook = DiscordWebhook(
            DISCORD_WEBHOOK,
            username="nasabot",
            content=(
                f"{DISCORD_MOD_ID} Submission titled"
                f" '[{submission.title}](https://reddit.com{submission.permalink})'"
                f" has hit /r/all index of {index}"
            ),
        )
        webhook.execute()

    except praw.exceptions.PRAWException as error:
        logging.warning(
            'Exception "%s" for id %s with title %s',
            error,
            submission.id,
            submission.title,
        )


if __name__ == "__main__":
    main()
    del db
