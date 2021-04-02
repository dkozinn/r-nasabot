"""
initialize discord info

Uses praw.ini file since we're using it already

"""
# pylint: disable=invalid-name

import configparser
import os

config = configparser.ConfigParser()
config_path = os.path.join(os.environ["HOME"], ".config", "praw.ini")
config.read(config_path)
webhook = config['nasapostbot']['discord_webhook']
