#!/usr/bin/python3

"""Display contents of posts.db"""

from datetime import datetime
from pathlib import Path

import praw
import praw.exceptions

import dbstuff

SUB = "nasa"
DBDIR = str(Path.home()) + "/" + SUB
db = dbstuff.NasaDB(DBDIR)
reddit = praw.Reddit("nasabot")
subreddit = reddit.subreddit(SUB)


def main():
    """Main loop"""

    results = db.fetch_all()

    for item in results:
        print(datetime.fromtimestamp(item[2]).strftime('%Y-%m-%d %H:%M:%S '), end='')
        print(f"Rank={item[1]}: {reddit.submission(id=item[0]).url}")


if __name__ == "__main__":
    main()
    del db
