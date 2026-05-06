"""Tests for nasautils.utilities (no live services)."""

from unittest.mock import MagicMock, patch

import apprise.common
import pytest

from nasautils.utilities import DEFAULT_NOTIFY_TITLE, get_sub, notify


def test_get_sub_default_argv():
    with patch("nasautils.utilities.sys.argv", ["script.py"]):
        assert get_sub() == "nasa"


def test_get_sub_from_argv():
    with patch("nasautils.utilities.sys.argv", ["script.py", "FooBar"]):
        assert get_sub() == "foobar"


@pytest.fixture
def no_apprise_config(monkeypatch, tmp_path):
    monkeypatch.delenv("APPRISE_URL", raising=False)
    monkeypatch.setattr(
        "nasautils.utilities.os.path.expanduser",
        lambda _p: str(tmp_path / "no_such_home"),
    )


def test_notify_skips_without_config_or_env(no_apprise_config):
    with patch("nasautils.utilities.os.path.exists", return_value=False):
        assert notify("hello") is False


def test_notify_uses_explicit_url_when_no_config_file(no_apprise_config):
    with patch("nasautils.utilities.os.path.exists", return_value=False):
        with patch("nasautils.utilities.apprise.Apprise") as mock_cls:
            mock_app = MagicMock()
            mock_app.notify.return_value = True
            mock_cls.return_value = mock_app

            assert notify("body", title="T", priority=1, url="json://localhost") is True

            mock_cls.assert_called_once()
            mock_app.add.assert_called_once_with("json://localhost")
            mock_app.notify.assert_called_once()
            kwargs = mock_app.notify.call_args[1]
            assert kwargs["title"] == "T"
            assert kwargs["body"] == "body"
            assert kwargs["notify_type"] == apprise.common.NotifyType.FAILURE


def test_notify_default_title(no_apprise_config):
    with patch("nasautils.utilities.os.path.exists", return_value=False):
        with patch("nasautils.utilities.apprise.Apprise") as mock_cls:
            mock_app = MagicMock()
            mock_app.notify.return_value = True
            mock_cls.return_value = mock_app

            notify("only body", url="json://localhost")
            kwargs = mock_app.notify.call_args[1]
            assert kwargs["title"] == DEFAULT_NOTIFY_TITLE


def test_notify_priority_zero_is_info(no_apprise_config):
    with patch("nasautils.utilities.os.path.exists", return_value=False):
        with patch("nasautils.utilities.apprise.Apprise") as mock_cls:
            mock_app = MagicMock()
            mock_app.notify.return_value = True
            mock_cls.return_value = mock_app

            notify("x", priority=0, url="json://localhost")
            kwargs = mock_app.notify.call_args[1]
            assert kwargs["notify_type"] == apprise.common.NotifyType.INFO


def test_notify_loads_config_file_when_present(monkeypatch, tmp_path):
    cfg_path = tmp_path / "apprise"
    cfg_path.write_text("json://localhost\n", encoding="utf-8")
    monkeypatch.delenv("APPRISE_URL", raising=False)
    monkeypatch.setattr(
        "nasautils.utilities.os.path.expanduser",
        lambda _p: str(cfg_path),
    )
    with patch("nasautils.utilities.apprise.Apprise") as mock_apprise:
        with patch("nasautils.utilities.apprise.AppriseConfig") as mock_cfg_cls:
            mock_cfg = MagicMock()
            mock_cfg_cls.return_value = mock_cfg
            mock_app = MagicMock()
            mock_app.notify.return_value = True
            mock_apprise.return_value = mock_app

            assert notify("hi", title="alert") is True

            mock_cfg.add.assert_called_once_with(str(cfg_path))
            mock_app.add.assert_called_once_with(mock_cfg)
