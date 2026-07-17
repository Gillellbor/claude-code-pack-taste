---
title: "Cursor adapter - install notes for the bootstrap integrator"
summary: "Exactly where each file in adapters/cursor/ lands on a user's machine, and what the bootstrap must template/resolve at install time."
status: draft
type: devops
version: "0.1.0"
release: latest
tags: [starter-pack, cursor, dev-tools, bootstrap]
created: 2026-07-14 00:00
updated: 2026-07-14 00:00
owner: Šimon Hradní
client: ~
path: adapters/cursor/install-notes.md
---

# Cursor adapter - install notes

For whoever wires this adapter into `bootstrap/INSTALL.md`. Six files ship in
this directory; none of them are wired into anything yet - the bootstrap does
the actual copying/rewriting described below.

## File-by-file destination

| Source (this dir) | Destination | Notes |
|---|---|---|
| `hooks.json` | `~/.cursor/hooks.json` (user-level, recommended) or `<project>/.cursor/hooks.json` (project-level) | See "Path resolution" below - the shipped `command` values must be checked against the real install path before being trusted verbatim. |
| `cursor_safety_hook.py` | `~/.cursor/safety/cursor_safety_hook.py` | Lives alongside the shared core (next row), matching Claude Code's own `~/.claude/safety/safety_check.py` convention. |
| (shared core, not in this dir) `kernel/safety/safety_check.py` | `~/.cursor/safety/safety_check.py` | Copy this in for every tool, not just Claude Code - Cursor's wrapper imports it by file, it does not read it via any Cursor-native mechanism. Identical bytes to the Claude Code install; do not fork it per tool. |
| `rules/pack-baseline.mdc` | `<project>/.cursor/rules/pack-baseline.mdc` | Per-project, not per-machine - see PARITY.md #2 for why. Every project the bootstrap sets up for this user needs its own copy. |
| `sandbox.json` | `<project>/.cursor/sandbox.json` (project-level) or `~/.cursor/sandbox.json` (user-level, applies to all workspaces) | Optional layer - safe to skip entirely if the user does not want the OS jail; the hook is the enforcement either way. Project-level overrides user-level when both exist (Cursor's own precedence rule). |
| `PARITY.md` | Not installed to the user's machine - reference doc for whoever maintains this adapter, and worth surfacing to the user once at install time ("here is exactly what Cursor does and does not enforce"). | |

## Path resolution - `~` in `hooks.json`'s `command` field is unconfirmed for Cursor

`hooks.json` ships with `"command": "python3 ~/.cursor/safety/cursor_safety_hook.py"`,
matching the exact convention `kernel/settings.json` already uses for Claude
Code (`"command": "~/.claude/safety/safety_check.py --tool claude"`) - so this
mirrors an already-working in-repo precedent, not a new guess. **However**,
whether Cursor's hook executor expands `~` the same way Claude Code's does is
not confirmed by anything read for this adapter. If the bootstrap can cheaply
verify this on a real Cursor install, do so once and record the result here.
Until then, treat literal `~` as the default and the safer fallback as:
substitute the actual resolved absolute home path (e.g.
`/Users/<user>/.cursor/safety/cursor_safety_hook.py` or
`C:\Users\<user>\.cursor\safety\cursor_safety_hook.py`) into `hooks.json` at
write time, the same way the bootstrap already has to resolve real paths for
everything else it installs.

## Windows: `python3` vs `python`

The shipped `command` uses `python3`, matching this repo's own shebang
convention (`kernel/safety/safety_check.py` starts `#!/usr/bin/env python3`)
and matching macOS/Linux defaults. **Native Windows commonly has no `python3`
on `PATH`** (only `python` or the `py` launcher). The bootstrap's OS-detection
step (`INSTALL.md` step 1: "Detect (or ask) the host tool + OS + shell") must
substitute `python` (or `py -3`) for `python3` in `hooks.json`'s `command`
field when installing on native Windows. No change needed for WSL2 (behaves
like Linux).

## `AGENTS.md` at the workspace level, not the home dir

Cursor reads `AGENTS.md` natively at the project root already - nothing to
install for that beyond what the bootstrap already does when it scaffolds a
project (copying/linking the pack's `kernel/AGENTS.md` content in). The only
new piece here is `rules/pack-baseline.mdc`, which exists specifically because
Cursor has no global (home-dir) rules file - see PARITY.md #2. Do not attempt
to place anything Cursor-specific at `~/.cursor/AGENTS.md` or similar; it does
not exist as a concept for Cursor for global behavior.

## `failClosed: true` - a deliberate choice, not a placeholder

`hooks.json` sets `failClosed: true` on both hook entries. This is intentional
(see PARITY.md #1: Cursor has no native deny-list backstop the way Claude Code
and Codex do, so a silently-failing hook here means zero deterministic
protection, not degraded protection). Do not "fix" this to `false` to reduce
friction without re-reading that section first.

## Verification the bootstrap should run per install (mirrors the design spec's per-tool checklist)

1. A destructive command (e.g. `rm -rf` against a scratch path) is refused by
   Cursor's agent after the hook is wired.
2. `AGENTS.md` is actually being read - ask the agent something only stated
   there and confirm it reflects that content.
3. `rules/pack-baseline.mdc` is discoverable (Cursor's rules UI lists it as
   always-applied).
4. An existing `.cursor/hooks.json` / `.cursor/rules/` on the user's machine is
   backed up and merged, never blind-overwritten (same rule as every other
   tool in this pack).
