import json
import os
from base64 import b64encode

from urllib.parse import quote_plus

import requests
from betamax import cassette
from betamax import Betamax

import praw

PRAW_CONFIG_SECTION = "nasapostbot"
REQUEST_LIMIT = 15
SEEN_SIZE = 2500


class BoundedList(list):
    def __init__(self, max_size):
        super().__init__()
        self.max_size = max_size

    def append(self, item):
        if len(self) >= self.max_size:
            self.pop(0)
        super().append(item)


class PRAWDebugger:
    def __init__(self, reddit: praw.Reddit, cassette_dir: str = "cassettes"):
        self._cassette_index = 0
        self._session = requests.Session()
        self._session.headers["Accept-Encoding"] = "identity"
        self._reddit = reddit
        self._seen_items = BoundedList(SEEN_SIZE)
        self._cassette_dir = cassette_dir
        self._ensure_cassette_dir()
        self.recorder = Betamax(self._session)
        with Betamax.configure() as config:
            config.before_record(callback=self._filter_access_token)
            config.before_record(callback=self._ensure_interaction_limit)
            config.cassette_library_dir = self._cassette_dir
            config.default_cassette_options["record_mode"] = "all"

            for key, value in {
                k: getattr(self._reddit.config, k)
                for k in [
                    "client_id",
                    "client_secret",
                    "password",
                    "refresh_token",
                    "username",
                ]
            }.items():
                if key == "password" and value:
                    value = quote_plus(value)
                if value:
                    config.define_cassette_placeholder(f"<{key.upper()}>", value)
            config.define_cassette_placeholder(
                "<BASIC_AUTH>",
                b64encode(
                    f"{self._reddit.config.client_id}:{self._reddit.config.client_secret}".encode()
                ).decode("utf-8"),
            )

    @staticmethod
    def _filter_access_token(interaction, current_cassette):
        """Add Betamax placeholder to filter access token."""
        response = interaction.data["response"]
        if response["status"]["code"] != 200:
            return
        try:
            body = response["body"]["string"]
            token = json.loads(body)["access_token"]
        except (KeyError, TypeError, ValueError):
            return
        current_cassette.placeholders.append(
            cassette.cassette.Placeholder(placeholder="<ACCESS_TOKEN>", replace=token)
        )

    @staticmethod
    def _ensure_interaction_limit(interaction, current_cassette):
        """Ensure that the number of interactions does not exceed REQUEST_LIMIT."""
        if len(current_cassette.interactions) >= REQUEST_LIMIT:
            current_cassette.interactions.pop(0)

    def _ensure_cassette_dir(self):
        if not os.path.exists(self._cassette_dir):
            os.makedirs(self._cassette_dir, exist_ok=True)

    @property
    def reddit(self):
        all_settings = self._reddit.config.__dict__
        custom_settings = all_settings.pop("custom", {})
        remaining_settings = all_settings.pop("_settings", {})
        return praw.Reddit(
            requestor_kwargs={"session": self._session},
            **all_settings,
            **custom_settings,
            **remaining_settings,
        )

    @property
    def cassette_index(self):
        if self._cassette_index == 0:
            try:
                with open(os.path.join(self._cassette_dir, ".cassette_index"), "r") as f:
                    self._cassette_index = int(f.read().strip())
            except (FileNotFoundError, ValueError):
                self._cassette_index = 0
        return self._cassette_index

    @cassette_index.setter
    def cassette_index(self, value):
        self._cassette_index = value
        with open(os.path.join(self._cassette_dir, ".cassette_index"), "w") as f:
            f.write(str(value))


    def start(self):
        self.cassette_index += 1
        self.recorder.use_cassette(f"interactions_{self.cassette_index}")
        self.recorder.start()

    def stop(self):
        self.recorder.stop()

    def stream(self, func):
        self.start()
        for i in func:
            if i.id in self._seen_items:
                print("Out of order items detected")
                self.stop()
                self.start()
            self._seen_items.append(i.id)
            yield i


if __name__ == "__main__":
    debugger = PRAWDebugger(praw.Reddit(PRAW_CONFIG_SECTION))

    reddit = debugger.reddit

    for item in debugger.stream(
        reddit.subreddit("all").stream.submissions(skip_existing=True)
    ):
        ...
        # Process the item