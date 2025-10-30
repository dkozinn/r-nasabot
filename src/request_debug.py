import json
import requests
from prawcore import Requestor
from praw import Reddit


class JSONDebugRequestor(Requestor):
    def request(self, *args, **kwargs):
        response = super().request(*args, **kwargs)
        if 'access_token' not in response.json():
            print(json.dumps(response.json(), indent=4))
        return response

# reddit = Reddit(
#     ...,
#     requestor_class=JSONDebugRequestor
# )