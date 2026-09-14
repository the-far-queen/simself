# Local Bridge — Python (FastAPI)

## Purpose
- Accept raw text from browser / curl
- Forward nothing
- Persist nothing
- Acknowledge only

## Requirements
```bash
pip install fastapi uvicorn
```

## bridge.py

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

## Why This Is Correct
- **Plain text only**
- No schema assumptions
- No execution
- No security theater
- Easy to replace with Rust / Go later

This is literally: *stdin over HTTP*

---

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

---

## IDE Side (Reminder)
- Poll `/next` **or** subscribe internally later
- Treat payload as **untrusted proposal**
- Run through:
  - MTE
  - Controller
  - Sandbox
  - Build/Test/Q

---

## Explicit Non-Goals (Locked)

This bridge does **not**:
- Stream tokens
- Parse markdown
- Authenticate
- Know what code is
- Know what FieldCore is

That's intentional.

---

## Notes

- Port: 7071
- Protocol: Plain text over HTTP
- No persistence
- Simple queue-based
