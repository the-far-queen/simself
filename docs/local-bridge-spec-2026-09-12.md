# Local Bridge — spec (2026-09-12)

**Filed:** 2026-09-12 by Hermes for Bobby.
**Source:** `Desktop/SimSelf/bridge.py` (116 lines, 2,240 bytes — spec + code).
**Canonical code:** `simself/src/bridge.py` (53 lines, md5: `cdddee14ccd340c335a509256472c75c`) — code portion only.
**Status:** Spec extracted from combined source. Code unchanged in repo.

---

## Purpose

- Accept raw text from browser / curl
- Forward nothing
- Persist nothing
- Acknowledge only

This is **stdin over HTTP.** The bridge is a pipe, not a parser.

## Requirements

```bash
pip install fastapi uvicorn
```

## Design (53 lines of Python at `simself/src/bridge.py`)

```python
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import asyncio

app = FastAPI()

# Simple in-memory queue (replace later)
ingest_queue = asyncio.Queue()

@app.post("/ingest", response_class=PlainTextResponse)
async def ingest(request: Request):
    body = await request.body()
    if not body:
        return PlainTextResponse("EMPTY", status_code=400)

    text = body.decode("utf-8", errors="replace")

    # Enqueue raw text — no parsing, no trust
    await ingest_queue.put({
        "text": text,
        "headers": dict(request.headers)
    })

    return "ACK"

# Optional: IDE poll hook
@app.get("/next")
async def next_item():
    if ingest_queue.empty():
        return PlainTextResponse("", status_code=204)

    item = await ingest_queue.get()
    return item

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7071)
```

## Why This Is Correct (the load-bearing design rationale)

| Property | Rationale |
|---|---|
| **Plain text only** | No schema = no parsing at the boundary. The bridge is plumbing; parsing is downstream. |
| **No schema assumptions** | Receives whatever the sender sends. Trusts nothing. |
| **No execution** | Bridge never executes the text. Pass-through only. |
| **No security theater** | Local use only. Port 7071 on localhost. No auth (intentional non-goal). |
| **Easy to replace with Rust / Go later** | ~53 lines of FastAPI = throwaway prototype. Real implementation can be Go/Rust for performance. |

The bridge **does not tokenize** the incoming text. Raw bytes decoded as UTF-8 with replacement. The receiver (IDE/agent downstream) decides what to do.

## Connection to Bobby's lexical insight

Per Bobby 2026-09-12: "tokenization breaks language." This bridge **preserves language intact** at the boundary. The downstream consumer (SimSelf + PSB) does whatever composition it needs. The boundary respects that language is not a sequence of tokens — it's a primitive vocabulary + compositional rules.

## Usage

### From browser / JS
```js
fetch("http://localhost:7071/ingest", {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: llmOutputText
});
```

### From terminal
```bash
curl -X POST http://localhost:7071/ingest \
    -H "Content-Type: text/plain" \
    --data-binary @output.txt
```

## IDE / Agent Side (downstream consumer)

- Poll `/next` **or** subscribe internally later (HTTP/WebSocket upgrade)
- Treat payload as **untrusted proposal** (don't execute blindly)
- Run through:
  - MTE (Multi-Modal Type Embedding?)
  - Controller (constitutional axis check?)
  - Sandbox (if executable code)
  - Build / Test / Q (validation)

## Explicit Non-Goals (Locked)

This bridge does **not**:
- Stream tokens (no SSE / WebSocket)
- Parse markdown
- Authenticate (no API keys, no OAuth)
- Know what code is
- Know what FieldCore is

That's intentional. The bridge is a **byte pipe**, not a smart endpoint. Smart endpoints are downstream.

## Notes

- **Port:** 7071 (localhost only)
- **Protocol:** Plain text over HTTP
- **Persistence:** None (in-memory queue only)
- **Replacement path:** Rewrite in Rust or Go when performance matters

## Why this is in the canonical repo but spec is here

The Python code (`simself/src/bridge.py`, 53 lines) is committed. This spec doc captures the **design rationale** (the markdown surrounding the code in the original `Desktop/SimSelf/bridge.py`). Without the rationale, a future engineer might "improve" the bridge by adding schema validation, auth, or streaming — defeating the design's purpose.

## Connections to canonical

- `simself/src/bridge.py` — the implementation
- `simself/src/harness/` — the broader harness package
- `simself/docs/constitutional-growth-paradigm-2026-09-12.md` — FieldCore non-LLM substrate framing
- `vault/30-originals/bridge-original-2026-09-07.py` — original source preserved verbatim
- `vault/50-index/notes/simself-py/bridge.py.md` — prior per-file note

## Open questions

1. **Replace with Rust/Go?** Yes — when throughput becomes a concern. Bridge is throwaway prototype.
2. **WebSocket vs HTTP poll?** WebSocket = better for streaming. But explicit non-goal = no streaming. HTTP poll is correct for current architecture.
3. **Authentication?** No. Local-only. If exposed beyond localhost, add auth.

## My observations (Hermes)

1. **Bridge embodies "stdin over HTTP" — the simplest possible pipe.** The author of this spec (Bobby) understands that **bridges should be stupid**. Smart endpoints are downstream.
2. **No tokenization at the boundary is principled.** The bridge preserves language intact. Parsing is downstream responsibility. This aligns with Bobby's lexical insight that tokenization breaks language.
3. **In-memory queue with `asyncio.Queue`** is the simplest correct concurrency primitive. Replaceable with any backend (Redis, Kafka, file). The current impl is ~30 lines; the replacement could be zero if you just `print()`.
4. **Explicit non-goals are load-bearing.** Without "we don't auth, we don't parse, we don't stream," a future engineer would "improve" the bridge by adding exactly those. The non-goals lock the design.
5. **53-line FastAPI is the prototype form.** Real implementation = Go or Rust. The Python version exists to make the design easy to read and modify. Not a performance target.

## Filed by

*Hermes, 2026-09-12. Source: `Desktop/SimSelf/bridge.py` (116 lines, 2,240 bytes — combined spec + code). Spec extracted to `simself/docs/local-bridge-spec-2026-09-12.md` (this file). Code is unchanged in `simself/src/bridge.py` (md5 match). Mirror: `vault/20-mirrors/simself/docs/local-bridge-spec-2026-09-12.md` (to be created on push). Original preserved: `vault/30-originals/bridge-original-2026-09-07.txt` (md5 match with Desktop).*

## Commit

Pending: `docs: local-bridge-spec-2026-09-12` (extracted from `Desktop/SimSelf/bridge.py` combined source).