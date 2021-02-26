#!/usr/bin/python3

from distutils.util import strtobool
from re import sub
import sys
import logging

import praw

SUB="nasa"
REPLY_TEMPLATE= ("If you're visiting here perhaps for the first time from /r/all, "
                "welcome to /r/nasa! Please take a moment to "
                "[read our welcome post](https://www.reddit.com/r/nasa/comments/l43hoq/welcome_to_rnasa_please_read_this_post_for/)"
                " before posting, and we hope you'll stick around for a while.")
FLAIR_TEMPLATE_ID="7216c708-7c40-11e4-b13d-12313d052165"
#FLAIR_TEMPLATE_ID="b37f60b8-74ac-11eb-9178-0e509773c193" #TOY

def main():
    reddit = praw.Reddit("nasabot")
    debug_level = reddit.config.custom['app_debugging'].upper()
    logging.basicConfig(level=debug_level)
    handler = logging.StreamHandler()
    handler.setLevel(debug_level)
    for logger_name in ("praw", "prawcore"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(debug_level)
        logger.addHandler(handler)

# Iterate through submissions, process if it's the right subreddit and it either has no flair or it has flair not matching the template

    for submission in reddit.subreddit('all').hot(limit=250):
        logging.info("Post in /r/"+str(submission.subreddit)+":"+submission.title+"/"+submission.id)
        if (submission.subreddit == SUB 
                and getattr(submission,'link_flair_template_id',"NONE") != FLAIR_TEMPLATE_ID):
             process_submission(submission)

def process_submission(submission):
    logging.info("Replying in /r/"+str(submission.subreddit)+":"+submission.title+"/"+str(submission.author)+"/"+submission.id)
    try:
        comment=submission.reply(REPLY_TEMPLATE)
        comment.mod.distinguish(how="yes",sticky=True)
        submission.mod.flair(flair_template_id=FLAIR_TEMPLATE_ID,text="/r/all")
    except praw.exceptions.PRAWException as e:
        logging.warning("Exception \"%s\" for id %s with title %s",e,submission.id,submission.title)

if __name__ == "__main__":
    main()