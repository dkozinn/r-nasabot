#!/bin/bash

nohup python nasapostbot.py nasajobs > /big/postbot.nasajobs &
nohup python nasapostbot.py nasa > /big/postbot.nasa &
nohup python nasaxpost.py > /big/xpostbot &
touch /big/started
