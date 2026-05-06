"""Tests for nasapostbot (PRAW + Discord mocked)."""

from unittest.mock import MagicMock, patch

import nasapostbot


def _mock_reddit():
    reddit = MagicMock()
    reddit.config.custom = {
        "app_debugging": "INFO",
        "praw_debugging": "WARNING",
        "discord_webhook": "https://discord.example/webhook",
    }
    return reddit


def test_main_posts_discord_for_recent_submission(monkeypatch):
    reddit = _mock_reddit()
    sub = MagicMock()
    sub.title = "Launch day"
    sub.permalink = "/r/nasa/comments/abc/launch/"
    sub.created_utc = 1_700_000_000.0
    sub.author.name = "nasa_official"

    monkeypatch.setattr(nasapostbot.time, "time", lambda: 1_700_000_100.0)

    def one_submission(**_kwargs):
        yield sub

    reddit.subreddit.return_value.stream.submissions = MagicMock(
        side_effect=one_submission
    )

    with patch("nasapostbot.praw.Reddit", return_value=reddit):
        with patch("nasapostbot.DiscordWebhook") as dw_cls:
            wh = MagicMock()
            dw_cls.return_value = wh
            nasapostbot.main()

    dw_cls.assert_called_once()
    wh.execute.assert_called_once()


def test_main_skips_stale_submission(monkeypatch):
    reddit = _mock_reddit()
    sub = MagicMock()
    sub.title = "Old news"
    sub.permalink = "/r/nasa/comments/old/x/"
    sub.created_utc = 1_000_000_000.0
    sub.author.name = "x"

    monkeypatch.setattr(nasapostbot.time, "time", lambda: 1_700_000_000.0)

    def one_submission(**_kwargs):
        yield sub

    reddit.subreddit.return_value.stream.submissions = MagicMock(
        side_effect=one_submission
    )

    with patch("nasapostbot.praw.Reddit", return_value=reddit):
        with patch("nasapostbot.DiscordWebhook") as dw_cls:
            nasapostbot.main()

    dw_cls.assert_not_called()
