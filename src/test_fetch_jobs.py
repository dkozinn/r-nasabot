"""Tests for nasautils.fetch_jobs (requests mocked; no live USAJobs API)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from nasautils import fetch_jobs as fj


def _sample_item(
    *,
    title="Astronaut",
    pos_id="NASA-123",
    uri="https://example.invalid/job",
    org="NASA",
    low=11,
    high=12,
    summary="Boldly go.",
):
    return {
        "MatchedObjectDescriptor": {
            "PositionTitle": title,
            "PositionID": pos_id,
            "PositionURI": uri,
            "JobGrade": [{"Code": "GS"}],
            "OrganizationName": org,
            "UserArea": {
                "Details": {
                    "LowGrade": low,
                    "HighGrade": high,
                    "JobSummary": summary,
                }
            },
        }
    }


def test_connect_headers():
    h = fj.connect("user@example.com", "secret-key")
    assert h["Host"] == "data.usajobs.gov"
    assert h["User-Agent"] == "user@example.com"
    assert h["Authorization-Key"] == "secret-key"


@patch("nasautils.fetch_jobs.requests.get")
def test_fetch_jobs_empty(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "SearchResult": {"SearchResultCount": 0, "SearchResultItems": []}
    }
    mock_get.return_value = mock_resp

    assert fj.fetch_jobs("e@x.com", "k") == ""
    mock_get.assert_called_once()
    mock_resp.raise_for_status.assert_called_once()


@patch("nasautils.fetch_jobs.requests.get")
def test_fetch_jobs_formats_markdown(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultItems": [_sample_item()],
        }
    }
    mock_get.return_value = mock_resp

    out = fj.fetch_jobs("e@x.com", "k")
    assert "# Astronaut" in out
    assert "#### [NASA-123](https://example.invalid/job)" in out
    assert "Grade: GS-11/12" in out
    assert "###### NASA" in out
    assert "Boldly go." in out
    assert "-" * 40 in out


@patch("nasautils.fetch_jobs.requests.get")
def test_fetch_jobs_same_grade_no_high_suffix(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultItems": [
                _sample_item(low=9, high=9),
            ],
        }
    }
    mock_get.return_value = mock_resp

    out = fj.fetch_jobs("e@x.com", "k")
    assert "Grade: GS-9\n" in out


@patch("nasautils.fetch_jobs.requests.get")
def test_fetch_jobs_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("bad status")
    mock_get.return_value = mock_resp

    with pytest.raises(requests.HTTPError):
        fj.fetch_jobs("e@x.com", "k")
