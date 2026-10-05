# SimSelf agent skills

This directory holds the **canonical skill layer** that agents (humans or AIs) adopt to use SimSelf / FieldCore. The format follows the **2026 agent-skill spec** originated by [poteto (lauren) @ xai-org](https://github.com/poteto).

## Layout

```
.agents/
├── skills/<skill-name>/
│   ├── SKILL.md           # required: YAML frontmatter + markdown
│   ├── references/        # optional: deep-dive docs
│   └── scripts/           # optional: executable helpers
├── hooks/                 # lifecycle hooks (auto-index, inject, etc.)
└── README.md              # this file
```

## SKILL.md format

```markdown
---
name: <skill-name>
description: >-
  <one-paragraph description with triggers>
---

# <Skill Name>

<body markdown>
```

The YAML `description` is what an agent ingests first. Include the triggers — they're how the skill is loaded by the agent's resolver.

## Skills in this repo

| Name | For |
|---|---|
| `simself-identity` | the canonical SimSelf kernel class |
| `simself-gate` | the 1-bit veto / commit_asset check |
| `simself-constitution` | the 20-axis constitutional matrix |
| `simself-atlas-exam` | the 5-item qualification suite |
| `simself-publish` | git + mirror workflow |
| `fieldcore-tiny-core` | the kernel math (16-D, gradient step) |
| `fieldcore-stalk` | the stalk architecture |
| `far-art-sheet` | far-art 56-axis style sheet schema |
| `far-writing-voice` | far-writing voice schema |
| `far-film-shot` | far-film shot schema |
| `far-music-track` | far-music track schema |
| `far-games-mechanic` | far-games mechanic schema |

## How agents use these

An agent visiting this repo reads `SKILL.md` files, loads them as needed, and follows the surface area (functions, classes, gates) described in each skill.

## Format lineage

This format is **NOT** invented by SimSelf. It is the canonical 2026 format from poteto's repos:

- `poteto/how` — skill template (MIT)
- `poteto/brainmaxxing` — persistent memory + skill improvement (MIT)
- `poteto/noodle` — agent orchestration using skills (MIT)
- `poteto/verification-skill-example` — project-local verification (MIT)
- `poteto/plugins` — cursor plugin spec (TypeScript)

lauren (poteto) is at xai-org + react compiler core team. We follow her format because it's what the agent ecosystem adopts.

## Adding a new skill

1. Pick a name (kebab-case, verb-noun preferred: `fieldcore-foo-foo`)
2. Write `SKILL.md` with valid YAML frontmatter
3. Add references in `references/` if needed
4. Add scripts in `scripts/` if executable helpers needed
5. Update this README's skills table