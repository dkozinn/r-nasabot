#!/usr/bin/python3

from distutils.util import strtobool
import sys
import logging

import praw

SUB="TOY"
REPLY_TEMPLATE= ("If you're visiting here perhaps for the first time from /r/all, "
                "welcome to /r/nasa! Please take a moment to "
                "[read our welcome post](https://www.reddit.com/r/nasa/comments/l43hoq/welcome_to_rnasa_please_read_this_post_for/)"
                " before posting, and we hope you'll stick around for a while.")
FLAIR_TEMPLATE_ID="b37f60b8-74ac-11eb-9178-0e509773c193"

processed=[]        #Remember which submissions have already been processed

def main():
    reddit = praw.Reddit("nasabot")
    if strtobool(reddit.config.custom["app_debugging"]):
        logging.basicConfig(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        for logger_name in ("praw", "prawcore"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)

    for submission in reddit.subreddit('TOY').hot(limit=1):
        if submission.id in processed:
            pass
        else:
            processed.append(submission.id)
            process_submission(submission)

def process_submission(submission):
    if submission.subreddit == SUB:
        logging.info("Replying in /r/"+str(submission.subreddit)+" to "+submission.title+" from "+str(submission.author)+" with ID "+submission.id)
        submission.mod.flair(flair_template_id=FLAIR_TEMPLATE_ID)
        comment=submission.reply(REPLY_TEMPLATE)
        comment.mod.distinguish(how="yes",sticky=True)
# TODO Store submissions that have already been processed -- probably use a list

if __name__ == "__main__":
    main()