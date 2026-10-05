---
name: simself-publish
description: >-
  Use when the user wants to commit, push, or mirror a SimSelf/FieldCore change to GitHub
  + the local vault. Triggers: "publish", "commit", "push", "mirror", "github", "the-far-queen".
---

# SimSelf Publish — git workflow

The publish flow moves work between three surfaces: local clone → github → vault mirror.

## The surfaces

1. **local clone**: `C:\Users\HP\AppData\Local\hermes\work_repos\<repo>\`
2. **github**: `https://github.com/the-far-queen/<repo>`
3. **vault mirror**: `C:\Users\HP\AppData\Local\hermes\vault\10-minimax\20-mirrors\<repo>\`

All three must agree. Mirror is **bit-identical to github minus exclusions** (.git, models, *.onnx, *.wav, etc.).

## Workflow

```bash
# 1. edit files in work_repos/<repo>/
# 2. commit
cd C:/Users/HP/AppData/Local/hermes/work_repos/<repo>
git config user.email "hermes@the-far-queen.local"
git config user.name "hermes"
git add -A
git commit -m "<msg>"
git push origin main

# 3. mirror to vault (Python in execute_code)
import shutil, hashlib, os
src = r"C:\Users\HP\AppData\Local\hermes\work_repos\<repo>"
dst = r"C:\Users\HP\AppData\Local\hermes\vault\10-minimax\20-mirrors\<repo>"
SKIP_DIRS = {'.git','models','node_modules','__pycache__'}
SKIP_EXTS = {'.onnx','.npy','.npz','.bin','.wav','.mp3','.jpg','.jpeg','.png','.gif','.pdf','.mp4','.zip'}
for r,dirs,fs in os.walk(src):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    rel = os.path.relpath(r, src)
    d = os.path.join(dst, rel) if rel != '.' else dst
    os.makedirs(d, exist_ok=True)
    for f in fs:
        if os.path.splitext(f)[1].lower() in SKIP_EXTS: continue
        sp = os.path.join(r, f); dp = os.path.join(d, f)
        if os.path.exists(dp) and hashlib.md5(open(sp,'rb').read()).hexdigest() == hashlib.md5(open(dp,'rb').read()).hexdigest():
            continue
        shutil.copy2(sp, dp)
```

## Auth

GitHub PAT for `the-far-queen` is in `vault/20-writing/github-token-2026-09-26.md` (classic, expires 2026-11-25). Read from vault, do NOT paste in chat unless asked.

## Forbidden

- post to x.com / external services
- spend money
- delete without explicit consent
- duplicate Desktop files into public repos

## See also

- `sunrise-startup` HOW-TO-DO-RIGHT.md
- `simself-identity` — the steward