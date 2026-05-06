"""Tests for bot cli_main() wrappers (no live Reddit)."""

from unittest.mock import Mock

import prawcore
import pytest
from requests.exceptions import HTTPError

import nasajobsbot
import nasamodqbot
import nasapostbot
import nasaxpost


def test_nasajobsbot_cli_http_error_calls_notify(monkeypatch):
    monkeypatch.setattr(
        nasajobsbot, "main", Mock(side_effect=HTTPError("upstream"))
    )
    mock_notify = Mock()
    monkeypatch.setattr(nasajobsbot, "notify", mock_notify)

    with pytest.raises(SystemExit) as exc:
        nasajobsbot.cli_main()

    assert exc.value.code == 0
    mock_notify.assert_called_once()
    assert mock_notify.call_args[1]["title"] == "nasajobs HTTPError"
    assert mock_notify.call_args[1]["priority"] == 0


def test_nasajobsbot_cli_unexpected_error_calls_notify(monkeypatch):
    monkeypatch.setattr(nasajobsbot, "main", Mock(side_effect=RuntimeError("boom")))
    mock_notify = Mock()
    monkeypatch.setattr(nasajobsbot, "notify", mock_notify)

    with pytest.raises(SystemExit) as exc:
        nasajobsbot.cli_main()

    assert exc.value.code == 1
    mock_notify.assert_called_once()
    assert mock_notify.call_args[1]["title"] == "nasajobsbot crashed"
    assert mock_notify.call_args[1]["priority"] == 1


def test_nasajobsbot_cli_reddit_server_error(monkeypatch):
    monkeypatch.setattr(
        nasajobsbot,
        "main",
        Mock(side_effect=prawcore.exceptions.ServerError(Mock())),
    )

    with pytest.raises(SystemExit) as exc:
        nasajobsbot.cli_main()

    assert exc.value.code == 2


@pytest.mark.parametrize(
    "module,title",
    [
        (nasapostbot, "nasapostbot crashed"),
        (nasamodqbot, "nasa modqueue bot crashed"),
        (nasaxpost, "nasaxpost crashed"),
    ],
)
def test_generic_bot_cli_notify_on_error(module, title, monkeypatch):
    monkeypatch.setattr(module, "main", Mock(side_effect=ValueError("x")))
    mock_notify = Mock()
    monkeypatch.setattr(module, "notify", mock_notify)

    with pytest.raises(SystemExit) as exc:
        module.cli_main()

    assert exc.value.code == 1
    mock_notify.assert_called_once()
    assert mock_notify.call_args[1]["title"] == title
    assert mock_notify.call_args[1]["priority"] == 1


@pytest.mark.parametrize("module", [nasapostbot, nasamodqbot, nasaxpost])
def test_generic_bot_cli_reddit_error(module, monkeypatch):
    monkeypatch.setattr(
        module,
        "main",
        Mock(side_effect=prawcore.exceptions.ResponseException(Mock())),
    )

    with pytest.raises(SystemExit) as exc:
        module.cli_main()

    assert exc.value.code == 2
