"""Guestbook API: stores guestbook messages and a visit counter in Redis."""
import json
import os
import sys
import time

import redis
from flask import Flask, jsonify, request

# ---- Configuration ----------------------------------------------------------
HOST = os.environ.get("API_HOST", "127.0.0.1")
PORT = int(os.environ.get("API_PORT", "8000"))
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
# -----------------------------------------------------------------------------

MAX_MESSAGES = 50
REDIS_DOWN = f"Could not reach Redis at {REDIS_HOST}:{REDIS_PORT}"

app = Flask(__name__)
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.errorhandler(redis.ConnectionError)
def redis_unavailable(_error):
    print(REDIS_DOWN)
    return jsonify(error=REDIS_DOWN), 503


@app.get("/health")
def health():
    db.ping()
    return jsonify(status="ok")


@app.post("/visits")
def record_visit():
    return jsonify(visits=db.incr("visits"))


@app.get("/messages")
def list_messages():
    messages = [json.loads(m) for m in db.lrange("messages", 0, -1)]
    words = int(db.get("words_counted") or 0)
    return jsonify(messages=messages, words_counted=words)


@app.post("/messages")
def add_message():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()[:40]
    text = str(body.get("text", "")).strip()[:280]
    if not name or not text:
        return jsonify(error="Both a name and a message are required"), 400

    message = {"name": name, "text": text, "at": int(time.time())}
    db.lpush("messages", json.dumps(message))
    db.ltrim("messages", 0, MAX_MESSAGES - 1)
    db.lpush("jobs", text)  # picked up by the optional worker service
    db.ltrim("jobs", 0, 999)
    return jsonify(message), 201


if __name__ == "__main__":
    try:
        db.ping()
    except redis.ConnectionError:
        print(f"{REDIS_DOWN}. Is Redis running?", file=sys.stderr)
        sys.exit(1)
    print(f"Guestbook API listening on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT)
