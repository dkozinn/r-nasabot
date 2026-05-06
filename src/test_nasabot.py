"""Tests for nasabot (PRAW, DB, and Discord mocked; no live Reddit)."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import praw.exceptions
import prawcore.exceptions
import pytest


@pytest.fixture
def nasabot_ctx():
    """Load nasabot with module-level Reddit and DB replaced by mocks."""
    mock_reddit = MagicMock()
    mock_reddit.config.custom = {
        "discord_webhook": "https://discord.example/webhook",
        "discord_mod_id": "<@mod>",
        "app_debugging": "INFO",
        "praw_debugging": "WARNING",
    }
    mock_db = MagicMock()

    with patch("praw.Reddit", return_value=mock_reddit):
        with patch("dbstuff.NasaDB", return_value=mock_db):
            sys.modules.pop("nasabot", None)
            import nasabot  # noqa: PLC0415

            yield nasabot, mock_reddit, mock_db

    sys.modules.pop("nasabot", None)


def _submission(*, subreddit, sub_id, title, permalink, author="someone"):
    sub = SimpleNamespace(
        subreddit=subreddit,
        id=sub_id,
        title=title,
        permalink=permalink,
        author=author,
    )
    sub.reply = MagicMock()
    sub.mod = MagicMock()
    return sub


def test_main_skips_non_nasa_submissions(nasabot_ctx):
    nasabot, mock_reddit, mock_db = nasabot_ctx
    other = _submission(
        subreddit="pics", sub_id="p1", title="Pic", permalink="/r/pics/p1/"
    )
    mock_reddit.subreddit.return_value.hot.return_value = [other]

    nasabot.main()

    mock_db.get_rank.assert_not_called()
    mock_db.insert.assert_not_called()
    mock_db.update.assert_not_called()


def test_main_inserts_and_processes_new_nasa_submission(nasabot_ctx):
    nasabot, mock_reddit, mock_db = nasabot_ctx
    mock_db.get_rank.return_value = None

    sub = _submission(
        subreddit="nasa",
        sub_id="n1",
        title="Launch",
        permalink="/r/nasa/comments/n1/x/",
    )
    comment = MagicMock()
    sub.reply.return_value = comment

    mock_reddit.subreddit.return_value.hot.return_value = [sub]

    with patch.object(nasabot, "process_submission", wraps=nasabot.process_submission):
        with patch("nasabot.DiscordWebhook") as dw_cls:
            wh = MagicMock()
            dw_cls.return_value = wh
            with patch("nasabot.time.time", return_value=1_700_000_000):
                nasabot.main()

    mock_db.get_rank.assert_called_once_with("n1")
    mock_db.insert.assert_called_once_with("n1", 1, 1_700_000_000)
    sub.reply.assert_called_once()
    comment.mod.distinguish.assert_called_once_with(how="yes", sticky=True)
    comment.disable_inbox_replies.assert_called_once()
    sub.mod.flair.assert_called_once_with(
        flair_template_id=nasabot.FLAIR_TEMPLATE_ID, text="/r/all"
    )
    wh.execute.assert_called_once()


def test_main_updates_rank_when_improved_and_posts_discord(nasabot_ctx):
    nasabot, mock_reddit, mock_db = nasabot_ctx
    mock_db.get_rank.return_value = 50

    sub = _submission(
        subreddit="nasa",
        sub_id="n2",
        title="Orbit",
        permalink="/r/nasa/comments/n2/y/",
    )
    mock_reddit.subreddit.return_value.hot.return_value = [sub]

    with patch("nasabot.DiscordWebhook") as dw_cls:
        wh = MagicMock()
        dw_cls.return_value = wh
        with patch("nasabot.time.time", return_value=1_700_000_001):
            nasabot.main()

    mock_db.update.assert_called_once_with("n2", 1, 1_700_000_001)
    mock_db.insert.assert_not_called()
    sub.reply.assert_not_called()
    wh.execute.assert_called_once()
    assert "Updated /r/all index to 1" in dw_cls.call_args[1]["content"]


def test_main_no_update_when_rank_not_improved(nasabot_ctx):
    nasabot, mock_reddit, mock_db = nasabot_ctx
    mock_db.get_rank.return_value = 1

    sub = _submission(
        subreddit="nasa",
        sub_id="n3",
        title="Same",
        permalink="/r/nasa/comments/n3/z/",
    )
    mock_reddit.subreddit.return_value.hot.return_value = [sub]

    with patch("nasabot.DiscordWebhook") as dw_cls:
        nasabot.main()

    mock_db.update.assert_not_called()
    mock_db.insert.assert_not_called()
    dw_cls.assert_not_called()
    sub.reply.assert_not_called()


def test_main_request_exception_logged(nasabot_ctx):
    nasabot, mock_reddit, _mock_db = nasabot_ctx
    mock_reddit.subreddit.return_value.hot.side_effect = (
        prawcore.exceptions.RequestException(Exception("network"), (), {})
    )

    with patch.object(nasabot.logging, "warning") as mock_warn:
        nasabot.main()

    mock_warn.assert_called_once()
    assert "trying to get submissions" in mock_warn.call_args[0][0]


def test_process_submission_praw_exception_logs(nasabot_ctx):
    nasabot, _mock_reddit, _mock_db = nasabot_ctx
    sub = _submission(
        subreddit="nasa",
        sub_id="n4",
        title="Fail",
        permalink="/r/nasa/comments/n4/f/",
    )
    sub.reply.side_effect = praw.exceptions.PRAWException("rate limit")

    with patch.object(nasabot.logging, "warning") as mock_warn:
        nasabot.process_submission(sub, 42)

    mock_warn.assert_called_once()
    assert "n4" in mock_warn.call_args[0]
    assert "Fail" in mock_warn.call_args[0]
