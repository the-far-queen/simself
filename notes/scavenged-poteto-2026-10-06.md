# scavenged — poteto agent-skill lineage

**filed by:** hermes (minimax-m3)
**date:** 2026-10-06
**trigger:** bobby directive — "scavenge her 85 repos and grow simself in varied ways"

## who is poteto

poteto = **lauren**, software engineer at **@xai-org** (Grok team) and the
**react compiler core team**. 11,300 followers, 11 following, 85 public repos.
The 11 are the canonical world-leader set:

- wycats (Yehuda Katz) — Ember.js creator, jQuery/Rails core
- josevalim — Elixir creator
- sebmarkbage (Sebastian Markbåge) — Vercel, React core
- captbaritone (Jordan Eldredge) — Meta, made webamp.org
- gsathya — React, formerly V8/Google
- chrismccord — Phoenix framework creator
- gaearon (Dan Abramov) — React core, Redux
- ahejlsberg (Anders Hejlsberg) — **TypeScript creator**, C#/Delphi designer
- josephsavona — React + Relay at Meta
- mofeiZ
- anysphere — Cursor (AI IDE)

## what we scavenged

5 load-bearing repos, cloned to `C:/Users/HP/AppData/Local/hermes/work_repos/poteto-skill-template/`:

| repo | stars | what we take |
|---|---|---|
| `poteto/how` | 866 | skill template — the canonical SKILL.md format |
| `poteto/brainmaxxing` | 313 | persistent memory + skill improvement (Python) |
| `poteto/noodle` | 397 | agent orchestration using skills (Go) — 1,360 files |
| `poteto/verification-skill-example` | 128 | project-local verification skill |
| `poteto/plugins` | 84 | cursor plugin specification |

## what we adopted

The **SKILL.md format**: YAML frontmatter (`name`, `description` with triggers) + markdown body.

Adopted in `simself/.agents/skills/` with 11 skills:
- simself-identity, simself-gate, simself-constitution, simself-atlas-exam, simself-publish
- fieldcore-tiny-core, fieldcore-stalk
- far-art-sheet, far-writing-voice, far-film-shot, far-music-track, far-games-mechanic

## what we did NOT adopt (yet)

lauren's full stack also includes:
- **brain/** (Obsidian vault) — we use `vault/10-minimax/` instead
- **principles/** (operating principles) — we use `SOUL.md` + `USER.md`
- **plans/** (phased execution plans) — we use kanban via `kanban_create`/`kanban_complete`
- **hooks/** (lifecycle hooks) — we use `cronjob` + `process` backgrounding
- **worktree/** (git worktree per agent) — we use shared work_repos/<repo>/
- **adversarial-review** skill — could become simself-gate v2
- **scheduling** skill — kanban already does this

the noodle Go CLI (1,360 files) is too large to port 1:1. the schema is what we adopt.

## why this matters for simself

simself's **target audience is AI agents** (per Bobby 2026-09-11). lauren's
format IS the format the agent ecosystem adopts in 2026. if simself uses
her SKILL.md layout, every agent that has read any poteto skill can read
ours. zero impedance.

## related

- `.agents/README.md` — the skill layer overview
- `.agents/skills/<name>/SKILL.md` — the 11 adopted skills
- poteto's repos (mirror at work_repos/poteto-skill-template/)

## forbidden

we did NOT copy code from poteto's repos into simself. the format is
adopted; the code is hers. if we ever want to use noodle's Go runtime,
we cite + link, do not paste.