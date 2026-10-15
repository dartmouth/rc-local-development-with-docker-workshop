// Guestbook web: serves the page and forwards /api/* requests to the API service.
const path = require("path");
const express = require("express");

// ---- Configuration ---------------------------------------------------------
const HOST = process.env.WEB_HOST || "127.0.0.1";
const PORT = Number(process.env.WEB_PORT || 3000);
const API_URL = process.env.API_URL || "http://localhost:8000";
// ----------------------------------------------------------------------------

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/health", (_req, res) => res.json({ status: "ok" }));

// Everything under /api is passed through to the API service, minus the prefix.
// e.g. POST /api/messages  ->  POST http://localhost:8000/messages
app.use("/api", async (req, res) => {
  const hasBody = !["GET", "HEAD"].includes(req.method);
  try {
    const upstream = await fetch(API_URL + req.url, {
      method: req.method,
      headers: { "Content-Type": "application/json" },
      body: hasBody ? JSON.stringify(req.body) : undefined,
    });
    res.status(upstream.status).json(await upstream.json());
  } catch {
    const error = `Could not reach the API at ${API_URL}`;
    console.error(error);
    res.status(502).json({ error });
  }
});

app.listen(PORT, HOST, () => {
  console.log(`Guestbook web listening on http://${HOST}:${PORT}`);
});
