"""Tests for nasaxpost (PRAW mocked; no live Reddit)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import praw.exceptions

import nasaxpost


def _mock_reddit():
    reddit = MagicMock()
    reddit.config.custom = {
        "app_debugging": "INFO",
        "praw_debugging": "WARNING",
    }
    return reddit


def test_main_crossposts_recent_submission(monkeypatch):
    reddit = _mock_reddit()
    cross = SimpleNamespace(
        title="News",
        author=MagicMock(),
        permalink="/r/nasa/comments/new/x/",
    )
    sub = SimpleNamespace(
        title="News",
        permalink="/user/nasa/comments/u1/x/",
        created_utc=1_700_000_000.0,
        author=MagicMock(),
    )
    sub.crosspost = MagicMock(return_value=cross)

    monkeypatch.setattr(nasaxpost.time, "time", lambda: 1_700_000_030.0)

    def one_sub(**_kwargs):
        yield sub

    reddit.subreddit.return_value.stream.submissions = MagicMock(side_effect=one_sub)

    with patch("nasaxpost.praw.Reddit", return_value=reddit):
        nasaxpost.main()

    sub.crosspost.assert_called_once()
    call_kw = sub.crosspost.call_args[1]
    assert call_kw["flair_id"] == "0f2362b2-7fae-11e3-bed4-22000aa47206"
    assert call_kw["send_replies"] is False


def test_main_skips_when_too_old(monkeypatch):
    reddit = _mock_reddit()
    sub = SimpleNamespace(
        title="Stale",
        permalink="/user/nasa/comments/old/x/",
        created_utc=1_000_000_000.0,
        author=MagicMock(),
    )
    sub.crosspost = MagicMock()

    monkeypatch.setattr(nasaxpost.time, "time", lambda: 1_700_000_000.0)

    def one_sub(**_kwargs):
        yield sub

    reddit.subreddit.return_value.stream.submissions = MagicMock(side_effect=one_sub)

    with patch("nasaxpost.praw.Reddit", return_value=reddit):
        nasaxpost.main()

    sub.crosspost.assert_not_called()


def test_main_invalid_crosspost_continues(monkeypatch):
    reddit = _mock_reddit()

    bad = SimpleNamespace(
        title="Bad",
        permalink="/user/nasa/comments/b1/x/",
        created_utc=1_700_000_000.0,
        author=MagicMock(),
    )
    bad.crosspost = MagicMock(
        side_effect=praw.exceptions.RedditAPIException(
            [praw.exceptions.RedditErrorItem("INVALID_CROSSPOST_THING")]
        )
    )

    cross = SimpleNamespace(
        title="Good",
        author=MagicMock(),
        permalink="/r/nasa/y/",
    )
    good = SimpleNamespace(
        title="Good",
        permalink="/user/nasa/comments/b2/x/",
        created_utc=1_700_000_000.0,
        author=MagicMock(),
    )
    good.crosspost = MagicMock(return_value=cross)

    monkeypatch.setattr(nasaxpost.time, "time", lambda: 1_700_000_030.0)

    def two_sub(**_kwargs):
        yield bad
        yield good

    reddit.subreddit.return_value.stream.submissions = MagicMock(side_effect=two_sub)

    with patch("nasaxpost.praw.Reddit", return_value=reddit):
        nasaxpost.main()

    assert bad.crosspost.call_count == 1
    good.crosspost.assert_called_once()
