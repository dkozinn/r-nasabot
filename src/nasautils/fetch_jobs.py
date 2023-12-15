#!/usr/bin/env python3
""" Returns markdown formatted jobs for NASA jobs from usajobs.gov"""

import requests

BASE_URL = "https://data.usajobs.gov/api/search?"


def main(email, key):
    """Fetches and prints jobs"""
    jobs = fetch_jobs(email, key)
    print(jobs)


def fetch_jobs(email: str, key: str):
    """
    Send an alert to a Discord channel about a new Reddit post

    Parameters:
        email: str - email address for usajobs.gov API access
        key: str - API key for usajobs.gov

    Returns:
        Markdown formatted string with job information
    """

    headers = connect(email, key)
    url = BASE_URL + "Organization=NN&DatePosted=1&Fields=Min&ResultsPerPage=50"
    resp = requests.get(url, headers=headers, timeout=30)
    data = resp.json()
    item_count = data["SearchResult"]["SearchResultCount"]
    result = ""
    for index in range(item_count):
        overview = data["SearchResult"]["SearchResultItems"][index][
            "MatchedObjectDescriptor"
        ]
        details = overview["UserArea"]["Details"]

        result += f'# {overview["PositionTitle"]}\n'
        result += f'#### [{overview["PositionID"]}]({overview["PositionURI"]})\n'
        result += f'Grade: {overview["JobGrade"][0]["Code"]}-{details["LowGrade"]}'
        if details["HighGrade"] > details["LowGrade"]:
            result += f'/{details["HighGrade"]}'
        result += "\n"
        result += f'###### {overview["OrganizationName"]}\n\n'
        result += f'{details["JobSummary"]}\n'

        result += "\n\n" + "-" * 40 + "\n\n"
    return result


def connect(email, apikey):
    """Forms the header parameters for authenticating with the v2 api."""
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,
        "Authorization-Key": apikey,
    }
    return headers


if __name__ == "__main__":
    import os

    try:
        main(os.environ["NJB_EMAIL"], os.environ["NJB_KEY"])
    except KeyError:
        print(
            (
                "Usage: python fetch_jobs.py\n"
                "Set environment variable NJB_EMAIL and NJB_KEY to the "
                "email and key associated with your usajobs.gov API developer account"
            )
        )
