"""Tests for nasamodqbot (PRAW + Discord mocked)."""

from unittest.mock import MagicMock, patch

import nasamodqbot


def _mock_reddit():
    reddit = MagicMock()
    reddit.config.custom = {
        "app_debugging": "INFO",
        "praw_debugging": "WARNING",
        "discord_webhook": "https://discord.example/webhook",
    }
    return reddit


def test_main_sends_modqueue_post_to_discord():
    reddit = _mock_reddit()
    sub = MagicMock()
    sub.title = "Reported post"
    sub.permalink = "/r/nasa/comments/xyz/report/"
    sub.author.name = "user1"
    sub.user_reports = []
    sub.link_title = "ignored"

    def one_item(**_kwargs):
        yield sub

    reddit.subreddit.return_value.mod.stream.modqueue = MagicMock(side_effect=one_item)

    with patch("nasamodqbot.praw.Reddit", return_value=reddit):
        with patch("nasamodqbot.DiscordWebhook") as dw_cls:
            wh = MagicMock()
            dw_cls.return_value = wh
            nasamodqbot.main()

    wh.execute.assert_called_once()
    content = dw_cls.call_args[1]["content"]
    assert "Reported post" in content
    assert "https://reddit.com/r/nasa/comments/xyz/report/" in content


def test_main_comment_modqueue_uses_link_title():
    reddit = _mock_reddit()
    sub = MagicMock(
        spec_set=["permalink", "author", "user_reports", "link_title"]
    )
    sub.permalink = "/r/nasa/comments/z/q/"
    sub.author.name = "critic"
    sub.user_reports = []
    sub.link_title = "Mars update"

    def one_item(**_kwargs):
        yield sub

    reddit.subreddit.return_value.mod.stream.modqueue = MagicMock(side_effect=one_item)

    with patch("nasamodqbot.praw.Reddit", return_value=reddit):
        with patch("nasamodqbot.DiscordWebhook") as dw_cls:
            wh = MagicMock()
            dw_cls.return_value = wh
            nasamodqbot.main()

    wh.execute.assert_called_once()
    assert "Mars update" in dw_cls.call_args[1]["content"]
