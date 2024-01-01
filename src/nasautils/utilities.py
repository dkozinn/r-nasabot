#!/usr/bin/python3

"""Misc utilities for r/nasa bot"""

import sys


def get_sub():
    """Get and return subreddit name"""
    if len(sys.argv) != 2:
        sub = 'nasa'
    else:
        sub = sys.argv[1:][0].lower()

    return sub
