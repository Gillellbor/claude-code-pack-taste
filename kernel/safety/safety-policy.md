---
title: "Canonical safety policy"
summary: "The single source of truth for what the pack blocks and why; every tool adapter realizes as much of it as its mechanism allows."
status: draft
type: core
version: "1.0.0"
release: latest
tags: [safety, dev-tools, starter-pack]
created: 2026-07-09 16:25
updated: 2026-07-09 16:25
owner: Šimon Hradní
client: ~
path: kernel/safety/safety-policy.md
---

# Canonical safety policy

Claude Code is the reference implementation. This document is the source of truth;
`safety_check.py` enforces it identically across every tool (wired into each tool's
pre-tool/pre-shell hook), and each tool's native deny-list (Claude `settings.json`,
Codex Rules) realizes as much of it as that mechanism allows. When a tool cannot
enforce a rule, its `PARITY.md` says so.

## What is blocked (enforced by `safety_check.py` in every tool)

1. **Reading secret env VALUES into context** - `cat`/`head`/`grep`/`source`/redirection/
   `python -c ...read()` and similar targeting `.env` / `.env.local` / `.env.production` / any
   `.env.*`. Exceptions: `.env.shared` (soft tier) and placeholder files
   (`.example`/`.sample`/`.template`/`.dist`). Referencing a file as config
   (`--env-file .env`, `cp .env.example .env`) is allowed - only reading values is blocked.
2. **Recursive + forced `rm` anywhere in a command** - including chained/embedded forms
   (`cd build && rm -rf .`) that a start-anchored deny rule misses.
3. **A plain `mv` that would silently overwrite an existing destination** - migration-safety.
4. **Download-and-execute / pipe-to-shell** - `curl|sh`, `wget|sh`, two-step fetch-then-exec.
5. **Subshell / eval bypasses carrying a destructive command** - `bash -c "...rm -rf..."`,
   `eval "...sudo..."`, `python -c` invoking `os.system`/`shutil.rmtree`/sensitive paths.
6. **Reading sensitive credential/keyring files via shell** - `~/.ssh` keys, `~/.aws/credentials`,
   `~/.gnupg`, `~/.git-credentials`, browser cookie/session stores.
7. **Destructive disk / system ops** - `dd` to a physical device, `mkfs.*`, `fdisk /dev/*`, fork bombs.
8. **Dangerous docker** - mounting host root (`-v /:/`), `--privileged`, mounting a sensitive host path
   (`.ssh`/`.aws`/`.gnupg`/`.kube`/`.docker`/`.config/gh`).

## What each tool adds natively (bonus second layer)

- **Claude Code:** `settings.json` `deny` (exact patterns) + `disableBypassPermissionsMode`.
- **Codex:** `rules/default.rules` Starlark `prefix_rule(...)` (prefix-match; a command hiding its
  real payload in shell substitution can dodge Rules, so `safety_check.py` is the backstop).
- **Cursor:** no deterministic native deny (its allowlist is an LLM classifier); the hook IS the deny.
  Optional `sandbox.json` OS-level boundary.
- **Antigravity:** coarse permission modes only; enforcement of this policy is unverified (best-effort).

## Why this is one file

If the block logic lived in five configs it would drift. It lives in `safety_check.py` (one enforced
brain) and this policy (one spec). Native deny-lists are convenience, not the guarantee.
