"""Guestbook worker (optional): counts the words in each new message."""
import os
import socket
import sys

import redis

# ---- Configuration ----------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
# -----------------------------------------------------------------------------

db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
worker_name = socket.gethostname()

try:
    db.ping()
except redis.ConnectionError:
    print(f"Could not reach Redis at {REDIS_HOST}:{REDIS_PORT}. Is Redis running?", file=sys.stderr)
    sys.exit(1)

print(f"[{worker_name}] waiting for new messages")
while True:
    _, text = db.brpop("jobs")  # blocks until the API queues a message
    words = len(text.split())
    total = db.incrby("words_counted", words)
    print(f"[{worker_name}] counted {words} words (total {total})")
