#!/usr/bin/env python3
"""Unit tests for nasajobsbot.py"""

from unittest.mock import MagicMock, Mock, patch

import pytest
import praw
import prawcore


@pytest.fixture(name="mock_reddit")
def _mock_reddit():
    """Mock Reddit instance with custom config"""
    reddit = MagicMock()
    reddit.config.custom = {
        "app_debugging": "INFO",
        "praw_debugging": "WARNING",
        "jobs_email": "test@example.com",
        "jobs_key": "test_key_12345",
    }
    return reddit


@pytest.fixture(name="mock_subreddit")
def _mock_subreddit():
    """Mock subreddit instance"""
    subreddit = MagicMock()
    return subreddit


def test_main_with_jobs(mock_reddit, mock_subreddit):
    """Test main function when jobs are found"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    jobs_content = "# Test Job 1\n## Job ID 12345\n\n# Test Job 2\n## Job ID 67890\n"

    with patch("nasajobsbot.fetch_jobs", return_value=jobs_content):
        with patch("praw.Reddit", return_value=mock_reddit):
            with patch("nasajobsbot.logging.info") as mock_log:
                main()

    # Verify subreddit.submit was called
    mock_subreddit.submit.assert_called_once()
    call_args = mock_subreddit.submit.call_args

    # Verify submission parameters
    assert "New usajobs.gov NASA postings as of" in call_args[0][0]
    assert call_args[1]["flair_text"] == "usajobs.gov"
    assert call_args[1]["selftext"] == jobs_content
    assert call_args[1]["send_replies"] is False
    mock_log.assert_called_with("Posted daily new jobs")


def test_main_no_jobs(mock_reddit, mock_subreddit):
    """Test main function when no jobs are found"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("nasajobsbot.fetch_jobs", return_value=""):
        with patch("praw.Reddit", return_value=mock_reddit):
            with patch("nasajobsbot.logging.info") as mock_log:
                main()

    # Verify subreddit.submit was NOT called
    mock_subreddit.submit.assert_not_called()
    mock_log.assert_called_with("No jobs found")


def test_server_error_propagates(mock_reddit, mock_subreddit):
    """Test that server errors propagate from main"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("praw.Reddit", return_value=mock_reddit):
        with patch("nasajobsbot.fetch_jobs", side_effect=prawcore.exceptions.ServerError(Mock())):
            with pytest.raises(prawcore.exceptions.ServerError):
                main()


def test_response_exception_propagates(mock_reddit, mock_subreddit):
    """Test that response exceptions propagate from main"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("praw.Reddit", return_value=mock_reddit):
        with patch("nasajobsbot.fetch_jobs", side_effect=prawcore.exceptions.ResponseException(Mock())):
            with pytest.raises(prawcore.exceptions.ResponseException):
                main()


def test_reddit_api_exception_propagates(mock_reddit, mock_subreddit):
    """Test that Reddit API exceptions propagate from main"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    # RedditAPIException expects a list of error items (tuples or RedditErrorItem)
    error_items = [["error_code", "error_message", "error_field"]]

    with patch("praw.Reddit", return_value=mock_reddit):
        with patch("nasajobsbot.fetch_jobs", side_effect=praw.exceptions.RedditAPIException(error_items)):
            with pytest.raises(praw.exceptions.RedditAPIException):
                main()


def test_http_error_propagates(mock_reddit, mock_subreddit):
    """Test that HTTP errors propagate from main"""
    from nasajobsbot import main
    from requests.exceptions import HTTPError

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("praw.Reddit", return_value=mock_reddit):
        error = HTTPError("Connection timeout")
        with patch("nasajobsbot.fetch_jobs", side_effect=error):
            with pytest.raises(HTTPError):
                main()


def test_unexpected_error_propagates(mock_reddit, mock_subreddit):
    """Test that unexpected errors propagate from main"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("praw.Reddit", return_value=mock_reddit):
        error = ValueError("Unexpected error")
        with patch("nasajobsbot.fetch_jobs", side_effect=error):
            with pytest.raises(ValueError):
                main()


def test_fetch_jobs_called_with_correct_args(mock_reddit, mock_subreddit):
    """Test that fetch_jobs is called with config values"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("nasajobsbot.fetch_jobs", return_value="") as mock_fetch:
        with patch("praw.Reddit", return_value=mock_reddit):
            main()

            # Verify fetch_jobs was called with correct email and key
            mock_fetch.assert_called_once_with(
                "test@example.com",
                "test_key_12345"
            )


def test_subreddit_retrieved_correctly(mock_reddit, mock_subreddit):
    """Test that the correct subreddit is retrieved"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("nasajobsbot.fetch_jobs", return_value=""):
        with patch("praw.Reddit", return_value=mock_reddit):
            main()

            # Verify subreddit was retrieved with correct name
            mock_reddit.subreddit.assert_called_once_with("nasajobs")


def test_keyboard_interrupt_propagates(mock_reddit, mock_subreddit):
    """Test that keyboard interrupt propagates from main"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("praw.Reddit", return_value=mock_reddit):
        with patch("nasajobsbot.fetch_jobs", side_effect=KeyboardInterrupt()):
            with pytest.raises(KeyboardInterrupt):
                main()


def test_submission_flair_id(mock_reddit, mock_subreddit):
    """Test that submission includes the correct flair ID"""
    from nasajobsbot import main

    mock_reddit.subreddit.return_value = mock_subreddit
    jobs_content = "# Test Job\n"

    with patch("nasajobsbot.fetch_jobs", return_value=jobs_content):
        with patch("praw.Reddit", return_value=mock_reddit):
            main()

            call_kwargs = mock_subreddit.submit.call_args[1]
            assert call_kwargs["flair_id"] == "c753e058-9ac6-11ee-a880-9a87da1d6157"


def test_title_format_with_date(mock_reddit, mock_subreddit):
    """Test that submission title includes today's date"""
    from nasajobsbot import main
    from datetime import date

    mock_reddit.subreddit.return_value = mock_subreddit
    jobs_content = "# Test Job\n"

    with patch("nasajobsbot.fetch_jobs", return_value=jobs_content):
        with patch("praw.Reddit", return_value=mock_reddit):
            main()

            call_args = mock_subreddit.submit.call_args[0]
            title = call_args[0]
            expected_date_str = date.today().strftime("New usajobs.gov NASA postings as of %A %B %-d, %Y")
            assert title == expected_date_str
