---
type: core
title: "_CLIENTS"
status: approved
summary: "One subdirectory per client engagement."
created: 2026-06-13 00:00
updated: 2026-06-13 00:00
owner: Šimon Hradní
client: ~
path: workspace/_CLIENTS/README.md
tags: [readme]
version: "1.0.0"
release: latest
---

# _CLIENTS

One subdirectory per client engagement.

## Don't run Claude from this directory

Claude should be invoked from a specific client subfolder (e.g. `~/Documents/_CLIENTS/acme-corp/`), not from `_CLIENTS/` itself. Each client has its own AGENTS.md / CLAUDE.md, knowledge base, projects — context is per-client, not shared.

If you start Claude here at the `_CLIENTS/` level, it has no specific client context and will likely produce generic output that doesn't match any of your engagements.

## Per-client structure

A scaffolded client directory looks like this:

```
acme-corp/
├── AGENTS.md                 ← canonical: client name, engagement type, scope, contacts
├── CLAUDE.md                 ← symlink to AGENTS.md
├── README.md                 ← changelog, current state, status
├── notes.md                  ← brain dump for this client (→ research auto-trigger)
├── log.md                    ← audit log of automations
├── docs/
│   ├── inbox/                ← drop documents here; Claude can ingest them into the KB when asked
│   │   └── done/             ← processed files moved here once ingested
│   ├── knowledge-base/       ← curated, AI-readable knowledge
│   │   └── drafts/           ← staging area for ingestion candidates
│   ├── meetings/             ← meeting transcripts, summaries
│   └── research/             ← topic-specific research outputs
├── projects/                 ← concrete projects for this client (one subfolder each)
└── research/                 ← generic research that doesn't fit a specific project
```

## Adding a new client

1. Copy `_example-client/` to a new directory named for the client (e.g. `acme-corp/`).
2. Edit `AGENTS.md` with the client's name, your engagement type, and scope.
3. Re-create the `CLAUDE.md` symlink: `cd acme-corp && ln -sfn AGENTS.md CLAUDE.md`.
4. Open Claude in that directory and start working.

Or use the `setup` skill: `cd ~/Documents/_CLIENTS/new-client/ && claude` then `/setup`.

## What auto-processes happen

- **`notes.md` with `→ research` marker** → auto-research dispatched, output to `research/`.

Requires `ANTHROPIC_API_KEY` in `~/.claude/.env`. Without it, the hook silently no-ops.

The `docs/inbox/` and `docs/inbox/done/` directories exist as a manual workflow — drop a file in `inbox/`, ask Claude to summarize and ingest it into `knowledge-base/drafts/`, move the source to `inbox/done/`. Not an automated hook in this pack (the upstream starter pack has an `inbox-processor` hook if you want it; this pack omits it by default to keep per-edit API costs predictable).

## What's NOT included

- No `scripts/` per client. Client-specific scripts go in `projects/{project}/scripts/` or `~/.claude/scripts/` for personal tools.
- No `.env` per client. Use `~/.claude/.env` (user-wide) and reference variable names in scripts via `~/.claude/scripts/list-env-keys.sh`.
- No tool-specific configs (package.json, pyproject.toml, etc.) at the client level — those live inside individual projects.
