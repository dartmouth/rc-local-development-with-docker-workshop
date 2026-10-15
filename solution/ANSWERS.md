# Instructor answer key

This folder mirrors the project root. To try the finished version, run this
from the project root:

```bash
cp -r solution/. .
podman compose up --build
```

If you'd rather attendees can't peek, move this folder onto a separate branch
before the workshop (`git checkout -b solution`, copy the files into place,
commit, then delete `solution/` from `main`).

## The gotchas, and what fixes them

**Bind address.** Both `web` and `api` default to listening on `127.0.0.1`.
Inside a container that's the container's own loopback, so nothing outside it
(not your browser, not another container) can connect. The symptom is a
connection reset or "empty reply" even though the port is published and the
logs say the server is running. Fix: set `WEB_HOST` / `API_HOST` to `0.0.0.0`.
Attendees usually hit this first, in step 1, when `podman run -p 8000:8000`
"works" but the browser can't connect.

**Service discovery.** `API_URL` defaults to `http://localhost:8000` and
`REDIS_HOST` to `localhost`. In a container, `localhost` is the container
itself. Fix: use the Compose service names (`http://api:8000`, `redis`). The
symptoms are clear on purpose: the API exits with "Could not reach Redis at
localhost:6379", and the page shows "Could not reach the API at
http://localhost:8000". Attendees saw the first of these in step 0, which is a
good thing to point out.

**Ports.** Only `web` needs a published port. `api` and `redis` only talk to
other containers. Publishing them isn't wrong, but it's worth asking why
they'd need it.

**Startup order.** The API pings Redis at startup and exits if it can't reach
it. Plain `depends_on` only waits for the Redis *container* to start, not for
Redis to accept connections. Fix: a Redis healthcheck plus
`condition: service_healthy`. In practice Redis starts quickly, so attendees
may not see the race locally; `restart: on-failure` is a reasonable
alternative answer, and it's worth discussing why real services often retry
anyway.

**Persistence.** Without a volume, `podman compose down` removes the Redis
container and its data, so the visit counter resets to 1. Fix: a named volume
on `/data`. `--appendonly yes` makes Redis write every change to disk rather
than snapshotting periodically. Note that `podman compose down -v` deletes the
volume too.

**Python log buffering.** When stdout isn't a terminal, Python buffers
`print()` output. The API's "listening on" line arrives late or not at all
(Flask's own request logs still show, since they go to stderr), and the
worker's log lines don't appear in `podman compose logs` at all. Fix:
`ENV PYTHONUNBUFFERED=1`, or `python -u`.

**Slow shutdown (PID 1 signals).** Each app runs as PID 1 in its container,
and PID 1 doesn't get the kernel's default signal handling. None of the apps
install a SIGTERM handler, so they ignore Podman's stop signal and get killed
after the 10 second timeout. Fix: `init: true` in Compose (or `--init` with
`podman run`), which runs a tiny init process that forwards signals. Running
`npm start` instead of `node server.js` makes this worse, since npm adds
another process in between.

## Podman notes

**Fully qualified image names.** Every image in the solution uses its full
`docker.io/library/...` name. Depending on the machine's
`registries.conf`, a short name like `redis:7-alpine` triggers an interactive
"which registry?" prompt, or an error in non-interactive contexts like
`podman compose`. The README gives attendees this as a tip so it doesn't eat
workshop time.

**`podman compose` is a wrapper.** It hands off to an external provider:
`docker-compose` if that's installed, otherwise `podman-compose`. Attendees
may end up with different providers, and they don't behave identically.
Before the workshop, check these against the provider you expect people to
have: `depends_on` with `condition: service_healthy`, `init: true`,
`profiles`, and `--scale`. Support for these in `podman-compose` has arrived
over several releases, so older versions may ignore or reject some of them.
`podman compose version` shows which provider is in use.

**Healthchecks need a timer.** Podman runs healthchecks via systemd timers.
On Linux hosts without systemd (some WSL setups, for example), healthchecks
never run on their own, so anything waiting on `service_healthy` waits
forever. On macOS and Windows the Podman machine VM handles this.

**`.containerignore` and docker-compose.** `podman build` and `podman-compose`
honor `.containerignore`. If the provider is `docker-compose`, the build
context is assembled by docker-compose itself, which only reads
`.dockerignore`. If attendees mix providers, a copy named `.dockerignore`
covers both.

## Stretch goal notes

- **`.containerignore`:** if an attendee ran `npm install` natively, copying
  `web/` without ignoring `node_modules` drags in their host's modules, which
  can include native binaries built for the wrong OS.
- **Layer caching:** copy the dependency manifest, install, then copy the code.
- **Bind mounts:** `podman-compose` doesn't support `compose watch`, so the
  live-reload stretch goal uses a bind mount instead. 
- **Scaling the worker:** `podman compose --profile worker up --scale worker=3`.
  Each replica logs its container hostname, so you can see Redis hand each
  message to exactly one of them.
- **Lockfile:** the sample ships without `package-lock.json`. Run `npm install`
  in `web/` once and commit the lockfile, then switch the Containerfile to
  `npm ci --omit=dev`. That's a good moment to talk about reproducible builds.
