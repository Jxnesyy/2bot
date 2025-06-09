#!/usr/bin/env python3
import os
from configparser import ConfigParser
import praw

cfg_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'reddit.ini')
cfg = ConfigParser(allow_no_value=True)
cfg.read(cfg_path)

redirect_uri = cfg.get('reddit', 'redirect_uri')
print("Config redirect_uri:", repr(redirect_uri))

reddit = praw.Reddit(
    client_id     = cfg.get('reddit','client_id'),
    client_secret = cfg.get('reddit','client_secret'),
    user_agent    = cfg.get('reddit','user_agent'),
    redirect_uri  = redirect_uri,
)

print("\nAuth URL:\n", reddit.auth.url(['identity'], state='TEST', duration='permanent'))
