#!/usr/bin/env python3
import os, sys, webbrowser
from configparser import ConfigParser
import praw

cfg = ConfigParser(allow_no_value=True)
cfg.read(os.path.join(os.path.dirname(__file__), '..', 'config', 'reddit.ini'))

reddit = praw.Reddit(
    client_id     = cfg.get('reddit', 'client_id'),
    client_secret = cfg.get('reddit', 'client_secret'),
    user_agent    = cfg.get('reddit', 'user_agent'),
    redirect_uri  = cfg.get('reddit', 'redirect_uri')
)

scopes = ['identity', 'read', 'submit']
auth_url = reddit.auth.url(scopes=scopes, state='...', duration='permanent')
print("1) Open this URL:\n\n", auth_url, "\n")
webbrowser.open(auth_url)

code = input("2) Paste the “code” parameter here: ").strip()
try:
    token = reddit.auth.authorize(code)
except Exception as e:
    print("Error:", e)
    sys.exit(1)

print("\n✅ Refresh token:\n", token)
