#!/usr/bin/env python3

import sys, os, re, csv
import time
import logging
from datetime import datetime
from configparser import ConfigParser
import praw
from prawcore import PrawcoreException, OAuthException

# === Paths & Config ===
BASE_DIR    = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config', 'reddit.ini')
LEADS_PATH  = os.path.join(BASE_DIR, '..', 'leads.csv')

def load_config(path):
    cfg = ConfigParser(allow_no_value=True)
    if not cfg.read(path):
        print(f"Error: Could not read config at {path}")
        sys.exit(1)
    return cfg

def setup_reddit(cfg):
    creds = {
        'client_id':     cfg.get('reddit','client_id'),
        'client_secret': cfg.get('reddit','client_secret'),
        'user_agent':    cfg.get('reddit','user_agent'),
    }
    token = cfg.get('reddit','refresh_token', fallback=None)
    if token:
        creds['refresh_token'] = token
    else:
        user = cfg.get('reddit','username', fallback=None)
        pwd  = cfg.get('reddit','password', fallback=None)
        if user and pwd:
            creds['username'] = user
            creds['password'] = pwd

    reddit = praw.Reddit(**creds)
    try:
        _ = reddit.user.me()  # validate
    except Exception as e:
        logging.error(f"Auth error: {e}")
        sys.exit(1)
    return reddit

# === Intent detection ===
CREATION_PATTERNS = [
    re.compile(r'\b(create|design|commission|custom)\b', re.I),
    re.compile(r'\b(digital art|illustration)\b', re.I),
]
MINTING_PATTERNS  = [
    re.compile(r'\b(mint|deploy|launch|list)\b', re.I),
    re.compile(r'\b(blockchain|open sea|opensea)\b', re.I),
]

def detect_intent(text: str):
    for pat in CREATION_PATTERNS:
        if pat.search(text):
            return 'creation'
    for pat in MINTING_PATTERNS:
        if pat.search(text):
            return 'minting'
    return None

# === Logging & CSV setup ===
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.info("nft_intel starting...")

def ensure_csv():
    if not os.path.exists(LEADS_PATH):
        with open(LEADS_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp','type','id','author','subreddit','intent','text'
            ])

def log_lead(item_type, obj, intent):
    ts = datetime.utcnow().isoformat()
    author = getattr(obj.author, 'name', '[deleted]')
    subreddit = obj.subreddit.display_name
    text = obj.title if item_type=='submission' else obj.body
    row = [ts, item_type, obj.id, author, subreddit, intent, text[:200]]
    with open(LEADS_PATH, 'a', newline='') as f:
        csv.writer(f).writerow(row)
    logging.info(f"Logged {item_type} {obj.id} [{intent}] by u/{author} in r/{subreddit}")

# === Main ===
def main():
    setup_logging()
    cfg = load_config(CONFIG_PATH)
    reddit = setup_reddit(cfg)

    subs = cfg.get('bot','subreddits', fallback='all')
    logging.info(f"Scraping r/{subs}…")
    subreddit = reddit.subreddit(subs)

    ensure_csv()

    while True:
        try:
            for submission in subreddit.stream.submissions(skip_existing=True):
                intent = detect_intent(submission.title + ' ' + (submission.selftext or ''))
                if intent:
                    log_lead('submission', submission, intent)
        except Exception as e:
            logging.error(f"Submission stream error: {e}")
            time.sleep(10)

        try:
            for comment in subreddit.stream.comments(skip_existing=True):
                intent = detect_intent(comment.body)
                if intent:
                    log_lead('comment', comment, intent)
        except Exception as e:
            logging.error(f"Comment stream error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()

