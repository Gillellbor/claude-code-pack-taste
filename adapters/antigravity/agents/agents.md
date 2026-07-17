---
title: "Antigravity workspace instruction file - bootstrap placeholder"
summary: "Placeholder noting that the bootstrap installer copies the canonical kernel/AGENTS.md content here rather than duplicating it by hand."
client: ~
status: ai-generated
type: core
version: "0.1.0"
release: latest
tags: [antigravity, agents-manifest, starter-pack, dev-tools]
created: 2026-07-14 10:49
updated: 2026-07-14 10:49
owner: Šimon Hradní
path: adapters/antigravity/agents/agents.md
---

# Antigravity workspace instruction file (bootstrap placeholder)

This file is a placeholder, not the real content. Antigravity's documented
workspace instruction file (in the IDE, at least - see `../WARNING.md` §1 for
why the desktop app reading it is unconfirmed) is `.agents/agents.md` -
exactly this path, relative to the workspace root.

**Do not hand-write behavioral content here.** The bootstrap installer
(`bootstrap/INSTALL.md`) copies the full, current content of the canonical
`kernel/AGENTS.md` into this location on install, the same way it produces
the `CLAUDE.md` symlink for Claude Code. That keeps one behavioral baseline
(`kernel/AGENTS.md`) as the single source of truth instead of a second,
independently-drifting copy living in this adapter.

Why a copy and not a symlink here: Claude Code's `CLAUDE.md -> AGENTS.md`
symlink works because both names sit in the same directory Claude Code reads.
Antigravity's `.agents/agents.md` lives at a different relative path inside
the target workspace, so the bootstrap step writes (or re-writes) a plain
copy of `kernel/AGENTS.md`'s content into `.agents/agents.md` at install
time - never edit that installed copy directly; edit `kernel/AGENTS.md` and
re-run the bootstrap so the copy stays in sync.

If you are reading this file as the actual `.agents/agents.md` in an
installed workspace, the bootstrap step did not run correctly - re-run
`bootstrap/INSTALL.md`'s Antigravity branch.
