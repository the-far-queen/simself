# Multi-Agent Debate IDE — Chorus (VSCode Fork of Roo Code)

**Source:** `Desktop/SimSelf/docs/multi-agent-ide-chorus.md` (11.6KB)
**Filed:** 2026-09-14 by Hermes for Bobby (re-mining pass)
**Status:** **engineering reference** — concrete build plan for multi-agent IDE fork

---

## Concept

VS Code extension fork of **Roo Code** that adds a **multi-agent panel** where 2–3 AI models review the same code simultaneously, debate each other's answers, and reach a synthesized verdict — all without leaving the editor.

**Codename: Chorus.**

---

## Repo setup

```bash
git clone https://github.com/RooVetGit/Roo-Code chorus
cd chorus
npm install
```

Key files to rename/rebrand:
- `package.json` → name: "chorus", displayName: "Chorus"
- `src/extension.ts` → entry point
- `src/core/` → agent orchestration logic
- `webview-ui/src/` → React panel UI

---

## New files to create

```
src/
├── agents/
│   ├── AgentManager.ts        ← multi-AI orchestration
│   ├── callers/
│   │   ├── MinimaxCaller.ts   ← Anthropic SDK + MiniMax base URL
│   │   ├── GeminiCaller.ts    ← spawns gemini CLI subprocess
│   │   └── OpenClawCaller.ts  ← local OpenAI-compatible port
│   └── modes/
│       ├── QuickMode.ts       ← parallel independent replies
│       ├── DebateMode.ts      ← round 1 + round 2 rebuttals
│       └── ChainMode.ts       ← sequential: A → B refines → C verdict
├── panels/
│   └── ChorusPanel.ts         ← VS Code WebviewPanel wrapper

webview-ui/src/
├── components/
│   ├── AgentColumn.tsx        ← one per AI, shows streaming reply
│   ├── DebateView.tsx         ← side-by-side R1 + R2
│   ├── ChainView.tsx          ← step-by-step chain with arrows
│   ├── ConsensusBar.tsx       ← green/yellow/red agreement
│   └── ModeSelector.tsx       ← Quick / Debate / Chain tabs
└── ChorusApp.tsx              ← root component
```

---

## AgentManager.ts — core logic

```typescript
export interface AgentReply {
  agent: "minimax" | "gemini" | "openclaw"
  round: number
  content: string
  durationMs: number
}

export class AgentManager {
  private callers = {
    minimax:  new MinimaxCaller(),
    gemini:   new GeminiCaller(),
    openclaw: new OpenClawCaller(),
  }

  // Round 1: all fire in parallel, no shared context
  async quickRound(prompt: string): Promise<AgentReply[]> {
    return Promise.all(
      Object.entries(this.callers).map(([agent, caller]) =>
        caller.call(prompt).then(content => ({
          agent, round: 1, content, durationMs: 0
        }))
      )
    )
  }

  // Round 2: each agent gets other agents' R1 replies as context
  async debateRound(
    originalPrompt: string,
    r1Results: AgentReply[]
  ): Promise<AgentReply[]> {
    return Promise.all(
      Object.entries(this.callers).map(([agent, caller]) => {
        const myR1     = r1Results.find(r => r.agent === agent)!
        const othersR1 = r1Results.filter(r => r.agent !== agent)
        const rebuttalPrompt = buildRebuttalPrompt(originalPrompt, myR1, othersR1)
        return caller.call(rebuttalPrompt).then(content => ({
          agent, round: 2, content, durationMs: 0
        }))
      })
    )
  }

  // Chain: sequential, each step sees all previous
  async *chainGenerator(prompt: string): AsyncGenerator<AgentReply> {
    const agents  = ["minimax", "gemini", "openclaw"] as const
    const history: AgentReply[] = []
    for (const agent of agents) {
      const chainPrompt = buildChainPrompt(prompt, history, agent)
      const content     = await this.callers[agent].call(chainPrompt)
      const reply       = { agent, round: history.length + 1, content, durationMs: 0 }
      history.push(reply)
      yield reply
    }
  }
}
```

---

## Caller pattern

```typescript
// src/agents/callers/MinimaxCaller.ts
import Anthropic from "@anthropic-ai/sdk"

export class MinimaxCaller {
  private client = new Anthropic({
    apiKey: process.env.MINIMAX_API_KEY ?? "",
    baseURL: "https://api.minimax.io/anthropic",
  })

  async call(prompt: string): Promise<string> {
    const msg = await this.client.messages.create({
      model:      "MiniMax-M2.5",
      max_tokens: 2048,
      system:     SYSTEM_PROMPT,
      messages:   [{ role: "user", content: prompt }],
    })
    return msg.content[0].type === "text" ? msg.content[0].text : ""
  }
}

// src/agents/callers/GeminiCaller.ts — CLI subprocess
import { execFile } from "child_process"
import { promisify } from "util"
const exec = promisify(execFile)

export class GeminiCaller {
  async call(prompt: string): Promise<string> {
    const { stdout } = await exec("gemini", ["-p", `${SYSTEM_PROMPT}\n\n${prompt}`])
    return stdout.trim()
  }
}

// src/agents/callers/OpenClawCaller.ts — local OpenAI-compatible
export class OpenClawCaller {
  private url = `http://localhost:${OPENCLAW_PORT}/v1/chat/completions`

  async call(prompt: string): Promise<string> {
    const res = await fetch(this.url, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model:    OPENCLAW_MODEL,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user",   content: prompt },
        ],
      }),
    })
    const data = await res.json()
    return data.choices[0].message.content
  }
}
```

---

## VS Code commands

Add to `package.json` `contributes.commands`:

```json
{
  "commands": [
    { "command": "chorus.quickReview",  "title": "Chorus: Quick Review (all agents)" },
    { "command": "chorus.debateReview", "title": "Chorus: Debate Review (2 rounds)" },
    { "command": "chorus.chainReview",  "title": "Chorus: Chain Review (sequential)" },
    { "command": "chorus.reviewSelection", "title": "Chorus: Review Selection" },
    { "command": "chorus.reviewFile",      "title": "Chorus: Review This File" }
  ],
  "menus": {
    "editor/context": [
      { "command": "chorus.reviewSelection", "when": "editorHasSelection" },
      { "command": "chorus.reviewFile" }
    ]
  }
}
```

---

## WebView panel UI

```
┌─────────────────────────────────────────────────────────────────┐
│  CHORUS  [ Quick ▼ ]  [ Debate ]  [ Chain ]        ⚙ Settings  │
├──────────────────┬──────────────────┬───────────────────────────┤
│  🔵 MiniMax M2.5 │  🟢 Gemini CLI   │  🟣 OpenClaw              │
│  Round 1:        │  Round 1:        │  Round 1:                 │
│  [streaming...]  │  [streaming...]  │  [streaming...]           │
│  Round 2:        │  Round 2:        │  Round 2:                 │
│  [rebuttal...]   │  [rebuttal...]   │  [rebuttal...]            │
├──────────────────┴──────────────────┴───────────────────────────┤
│  CONSENSUS  ████████████████████░░░░  75% agreement            │
│  ✅ All agree: use try/catch on line 14                         │
│  ⚠️  Split: MiniMax says memoize, Gemini disagrees             │
│  ❌ No consensus on variable naming                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## ConsensusBar logic

```typescript
export async function analyzeConsensus(replies: AgentReply[]): Promise<ConsensusResult> {
  // Send all replies to one fast model
  // Ask it to extract: agreed, disagreements, unresolved
  const prompt = `
    Three AI engineers reviewed the same code. 
    Extract: (1) points all three agree on, 
             (2) points where two agree and one disagrees,
             (3) points with no consensus.
    Reply in JSON only.
    Reviews:
    ${replies.map(r => `${r.agent}: ${r.content}`).join("\n\n")}
  `
  // Returns structured JSON with agreed[], split[], unresolved[]
}
```

---

## Settings

```typescript
{
  "chorus.minimax.apiKey":    "",
  "chorus.minimax.model":     "MiniMax-M2.5",
  "chorus.gemini.cliCommand": "gemini",
  "chorus.openclaw.port":     3000,
  "chorus.openclaw.model":    "default",
  "chorus.defaultMode":       "debate",
  "chorus.systemPrompt":      ""
}
```

---

## Phased build plan

| Phase | Scope | Effort |
|-------|-------|--------|
| 1 | AgentManager + 3 callers + basic side-by-side panel | ~2–3 days |
| 2 | Debate mode round 2 with context passing | ~1 day |
| 3 | Chain mode with streaming step-by-step UI | ~1–2 days |
| 4 | ConsensusBar + agreement analysis | ~1–2 days |
| 5 | Right-click menu, file review, settings panel | ~1 day |
| 6 | Polish, error handling, VSIX packaging | ~1 day |

**Total: ~1–2 weeks solo, faster with AI assistance.**

---

## vs. Roo Code

| Feature | Roo Code | Chorus |
|---------|----------|--------|
| Models at once | 1 | 2–3 |
| Models see each other | ❌ | ✅ |
| Debate / rebuttal round | ❌ | ✅ |
| Chain refinement | ❌ | ✅ |
| Consensus indicator | ❌ | ✅ |
| Gemini CLI (free tier) | ❌ | ✅ |
| Local agent support | partial | ✅ |

---

*Filed 2026-09-14 by Hermes. Per Bobby directive: buildable, scoped, cheap. Start with Phase 1 — get the panel showing three columns with live responses.*
