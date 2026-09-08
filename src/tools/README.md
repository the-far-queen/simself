# Tools

**Peripheral scripts.** Not part of SimSelf core. These are Bobby's pipeline utilities.

## chat_transcript_convert.py

Converts xAI/Grok companion JSON exports to dated markdown chat logs.

**Usage:**
```bash
python chat_transcript_convert.py                    # all *.json in cwd
python chat_transcript_convert.py path/to/folder/    # all *.json in folder
python chat_transcript_convert.py file.json          # single file
```

**Features:**
- Auto-detects speaker names from JSON (no hardcoded "James"/"Mika")
- Handles MongoDB extended JSON timestamps ($date, $numberLong)
- Handles multiple common JSON shapes (responses, messages, history, turns)
- Output: `<input>.md` written next to each input

**Output destination:** Bobby wants converted chats in `vault/10-minimax/50-index/notes/chat-transcripts/`. Pipe there after conversion:

```bash
python chat_transcript_convert.py ~/exports/
mv *.md ~/AppData/Local/hermes/vault/10-minimax/50-index/notes/chat-transcripts/
```

**Reference:** Based on M1K4_James x.com post (pattern). Hermes variant — auto-detect, multi-shape support.

## Adding tools

New tools go here. Must be:
- Standalone (no SimSelf core imports)
- Single-purpose
- Documented in this README