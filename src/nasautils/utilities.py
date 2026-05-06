#!/usr/bin/python3

"""Misc utilities for r/nasa bot"""

import logging
import os
import sys
from typing import Optional

import apprise


def get_sub():
    """Get and return subreddit name"""
    if len(sys.argv) != 2:
        sub = 'nasa'
    else:
        sub = sys.argv[1:][0].lower()

    return sub


DEFAULT_NOTIFY_TITLE = "NASAbots Notification"


def notify(
    body: str,
    *,
    title: Optional[str] = None,
    priority: int = 1,
    url: Optional[str] = None,
) -> bool:
    """
    Send a notification using Apprise.

    Args:
        body: Message body.
        title: Optional notification title; defaults to DEFAULT_NOTIFY_TITLE.

    Configuration:
    - By default, reads a plain-text Apprise config from `~/.config/apprise`
      (one URL per line), OR
    - Pass `url=...` explicitly, OR
    - Set `APPRISE_URL` in the environment (single URL or comma-separated URLs).

    Priority mapping (compatible with previous `ntfy -o priority N` usage):
    - 0: info
    - 1: failure
    """

    resolved_title = DEFAULT_NOTIFY_TITLE if title is None else title

    notify_type = apprise.common.NotifyType.FAILURE
    if priority <= 0:
        notify_type = apprise.common.NotifyType.INFO

    app = apprise.Apprise()

    config_path = os.path.expanduser("~/.config/apprise")
    if os.path.exists(config_path):
        cfg = apprise.AppriseConfig()
        cfg.add(config_path)
        app.add(cfg)
    else:
        urls = (url or os.getenv("APPRISE_URL", "")).strip()
        if not urls:
            logging.warning(
                "Notification skipped (no apprise config or APPRISE_URL): %s",
                resolved_title,
            )
            return False
        for entry in (u.strip() for u in urls.split(",") if u.strip()):
            app.add(entry)

    try:
        return bool(
            app.notify(title=resolved_title, body=body, notify_type=notify_type)
        )
    except Exception:  # pylint: disable=broad-except
        logging.exception("Apprise notify failed: %s", resolved_title)
        return False
