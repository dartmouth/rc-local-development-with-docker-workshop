# Guestbook: a sample app to containerize

A tiny guestbook. Visitors see a visit counter, read recent messages, and sign
the book. It's split into small services so you can practice containerizing
something with more than one moving part.

```
 browser ──▶  web (Node/Express, :3000)  ──▶  api (Python/Flask, :8000)  ──▶  redis (:6379)
                                                                               ▲
                                              worker (Python, optional) ───────┘
```

| Service  | What it does                                               | Files to look at                 |
|----------|------------------------------------------------------------|----------------------------------|
| `web`    | Serves the page and forwards `/api/*` calls to the API     | `web/server.js`                  |
| `api`    | Stores messages and the visit counter in Redis             | `api/app.py`                     |
| `redis`  | The database. No code here: you'll use an existing image   | (none)                           |
| `worker` | Optional. Counts words in new messages, off a Redis queue  | `worker/worker.py`               |

Every setting each service uses (host, port, where to find its dependency) is
in a **Configuration** block at the top of its file, and each one can be set
with an environment variable. You shouldn't need to read anything below those
blocks to get the app running in containers.

## Step 0: try to run it natively (optional)

You need Python 3.11+, Node 20+, and Redis. In three terminals:

```bash
# Terminal 1
redis-server

# Terminal 2
cd api
pip install -r requirements.txt
python app.py

# Terminal 3
cd web
npm install
npm start
```

Then open http://localhost:3000.

**Don't have Redis installed?** Most people don't. Before installing it, try
this instead, and then start the API again:

```bash
podman run --rm -p 6379:6379 docker.io/library/redis:7-alpine
```

Notice what just happened: a dependency that didn't exist on your machine is
now running, with nothing installed. The rest of this session is about doing
the same thing for the other services.

**Don't have Python or Node either?** That's fine. Skip ahead; you only need
Podman for the remaining steps.

## The exercise

1. **Containerize the API.** Write `api/Containerfile`, build it, and run it on its
   own with `podman run`. Can you reach http://localhost:8000/health from your
   browser?
2. **Containerize the web service.** Write `web/Containerfile`, build it, and run it.
3. **Bring it all together.** Write a `compose.yml` in the project root that
   runs `web`, `api`, and `redis`. The goal: `podman compose up` and the app
   works at http://localhost:3000.
4. **Start in the right order.** Make sure the API doesn't start before Redis is
   ready to accept connections.
5. **Keep your data.** Sign the guestbook, note the visit count, then run
   `podman compose down` and `podman compose up` again. Is everything still
   there? Make it so it is.

### Checklist: things that work natively but break in containers

Each of these will bite you at some point in the steps above. They're phrased
as questions on purpose.

- When a service says it's listening on `127.0.0.1`, who exactly can reach it?
  Is "localhost" inside a container the same as localhost on your laptop?
- When the web service looks for the API at `localhost:8000`, where is it
  actually looking once it's in a container? How do Compose services find each
  other?
- Which services actually need a port published to your machine, and which only
  need to talk to each other?
- The configuration blocks read environment variables. Where's the right place
  to set those: in the code, the Containerfile, or `compose.yml`?
- What does the API do if Redis isn't up yet when it starts? How can Compose
  know that Redis (not just its container) is ready?
- Where does Redis keep its data, and what happens to it when the container is
  removed?
- Do you see all the log output you expect in `podman compose logs`? Compare it
  with what you saw running natively.
- How long does `podman compose down` take? Is something ignoring the signal
  Podman sends it?

### Stretch goals

- Add `.containerignore` files. What happens to your image size and build time if
  `node_modules` gets copied in?
- Add the `worker` service. Then try `podman compose up --scale worker=3`, sign
  the guestbook a few times, and watch `podman compose logs -f worker` to see
  which replica picks up each message.
- Use a bind mount so edits to `server.js` or `app.py` show up without
  rebuilding the image by hand.
- Make the image build faster on code changes by ordering your Containerfile
  instructions so dependencies are cached.
