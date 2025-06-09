#!/usr/bin/env python3

import sys, os, re, time, logging
from datetime import datetime
from configparser import ConfigParser
import praw
from prawcore import PrawcoreException, OAuthException

# === Paths & Config ===
BASE_DIR    = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config', 'reddit.ini')
LOGS_DIR    = os.path.join(BASE_DIR, '..', 'logs')

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

def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    logfile = os.path.join(LOGS_DIR, f"engage_{datetime.now():%Y%m%d}.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)]
    )
    logging.info("nft_engage starting…")

# === State ===
replied_sub  = set()
replied_com  = set()
last_reply   = 0

# === Intent & Replies ===
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
        if pat.search(text): return 'creation'
    for pat in MINTING_PATTERNS:
        if pat.search(text): return 'minting'
    return None

def craft_reply(intent, link):
    if intent=='creation':
        return f"🎨 Need custom NFT art? Check my Fiverr gig 👉 {link} 👈 and let's bring your vision to life!"
    else:
        return f"🚀 Ready to mint your NFT collection? See my Fiverr service 👉 {link} 👈 to get started!"

# === Handlers ===
def handle_submission(sub, cfg, link):
    global last_reply
    name = sub.subreddit.display_name.lower()
    bl   = [s.strip().lower() for s in cfg.get('bot','blacklist', fallback='').split(',') if s]
    wl   = [s.strip().lower() for s in cfg.get('bot','whitelist', fallback='').split(',') if s]
    if name in bl or (wl and name not in wl): return
    if sub.id in replied_sub: return

    text = sub.title + ' ' + (sub.selftext or '')
    intent = detect_intent(text)
    if not intent: return

    # Rate-limit
    cooldown = cfg.getint('bot','cooldown_minutes',fallback=5)*60
    if time.time() - last_reply < cooldown: return

    reply = craft_reply(intent, link)
    try:
        sub.reply(reply)
        logging.info(f"Replied to submission {sub.id} [{intent}] in r/{name}")
        replied_sub.add(sub.id)
        last_reply = time.time()
    except Exception as e:
        logging.error(f"Failed replying to {sub.id}: {e}")

def handle_comment(cm, cfg, link):
    global last_reply
    name = cm.subreddit.display_name.lower()
    bl   = [s.strip().lower() for s in cfg.get('bot','blacklist',fallback='').split(',') if s]
    wl   = [s.strip().lower() for s in cfg.get('bot','whitelist',fallback='').split(',') if s]
    if name in bl or (wl and name not in wl): return
    if cm.id in replied_com: return

    intent = detect_intent(cm.body)
    if not intent: return

    cooldown = cfg.getint('bot','cooldown_minutes',fallback=5)*60
    if time.time() - last_reply < cooldown: return

    reply = craft_reply(intent, link)
    try:
        cm.reply(reply)
        logging.info(f"Replied to comment {cm.id} [{intent}] in r/{name}")
        replied_com.add(cm.id)
        last_reply = time.time()
    except Exception as e:
        logging.error(f"Failed replying to comment {cm.id}: {e}")

# === Main ===
def main():
    setup_logging()
    cfg  = load_config(CONFIG_PATH)
    reddit = setup_reddit(cfg)

    subs = cfg.get('bot','subreddits',fallback='all')
    link = cfg.get('bot','fiverr_link',
                   fallback='https://www.fiverr.com/nathanjones8676/design-deploy-and-launch-your-nft-collection')
    logging.info(f"Streaming r/{subs} for NFT engagement…")
    sr = reddit.subreddit(subs)

    while True:
        try:
            for post in sr.stream.submissions(skip_existing=True):
                handle_submission(post, cfg, link)
        except Exception as e:
            logging.error(f"Submission stream error: {e}")
            time.sleep(10)

        try:
            for cm in sr.stream.comments(skip_existing=True):
                handle_comment(cm, cfg, link)
        except Exception as e:
            logging.error(f"Comment stream error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()

