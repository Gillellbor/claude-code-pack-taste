---
title: "Antigravity adapter - install notes for the integrator"
summary: "Where these files would land on disk (workspace .agents/ vs global ~/.gemini/), Mac and Windows availability, and the mandatory hands-on verification step before trusting any of it."
client: ~
status: ai-generated
type: devops
version: "0.1.0"
release: latest
tags: [antigravity, dev-tools, starter-pack, setup-guide]
created: 2026-07-14 10:49
updated: 2026-07-14 10:49
owner: Šimon Hradní
path: adapters/antigravity/install-notes.md
---

# Antigravity adapter - install notes

For whoever wires this adapter into the future `bootstrap/INSTALL.md`
universal installer (not built yet - this adapter is standalone deliverables
only, per the design spec). Read `WARNING.md` and `PARITY.md` first; nothing
below changes the fact that this whole adapter is unverified.

## Where files would land

| Source (this repo) | Assumed destination | Confidence |
|---|---|---|
| `adapters/antigravity/agents/agents.md` | `<workspace>/.agents/agents.md`, populated with `kernel/AGENTS.md`'s current content by the bootstrap step (see `agents/agents.md`'s own header) | Medium - path matches documented IDE convention; desktop-app read is unconfirmed |
| `adapters/antigravity/hooks.json` | `<workspace>/.agents/hooks.json` | Low - shape is "mostly community-documented" per the research; no official schema found |
| `adapters/antigravity/antigravity_safety_hook.py` | `~/.gemini/safety/antigravity_safety_hook.py`, alongside a copy of `kernel/safety/` (mirrors Claude Code's `~/.claude/safety/safety_check.py` convention) | Low - this is this adapter's own assumption for where the bootstrap would place it, not something confirmed by Antigravity documentation |
| `kernel/safety/safety_check.py` + `safety-policy.md` | `~/.gemini/safety/` (global, shared across workspaces, same pattern as Claude Code's `~/.claude/safety/`) | Low - same caveat as above |

If the actual bootstrap step (when built) places these differently, update
`hooks.json`'s command path and/or set the `PACK_SAFETY_DIR` environment
variable so `antigravity_safety_hook.py` finds `safety_check.py` regardless
of exact install layout - that env var exists precisely to decouple the
wrapper from a specific assumed path.

## Global file collision - `~/.gemini/GEMINI.md`

Antigravity's documented global instruction file is `~/.gemini/GEMINI.md` -
the same hard-coded path the separate Gemini CLI tool uses for its own
global context. **Before writing anything to `~/.gemini/`, the installer
must check whether that file already exists and belongs to a Gemini CLI
install the user did not intend to touch**, and back it up / merge rather
than overwrite (per this pack's general migration-safety rule - never
blind-overwrite an existing config). See `WARNING.md` §2.

Source: https://github.com/google-gemini/gemini-cli/issues/16058

## Mac + Windows availability

The research this adapter is built from covers Antigravity 2 as a desktop
app (Mac confirmed via the product launch coverage); no Windows-specific
detail was found or verified for this adapter. `antigravity_safety_hook.py`
is pure Python 3 stdlib (no shell dependency), so the wrapper itself runs
identically on Mac, Linux, and native Windows once Python 3 is available -
consistent with this pack's cross-OS-via-Python principle. What is NOT
verified for Windows: whether `hooks.json`'s `command` field needs a
different invocation form (e.g. `python` vs `python3`), and whether the
desktop app's install location / config home differs from `~/.gemini/` on
Windows. Verify both before shipping a Windows install path.

## Mandatory: verify hands-on before trusting any of this

Do not treat this adapter as functional until you have personally confirmed,
inside a real Antigravity desktop app install, all of the following:

1. **The instruction file is actually read.** Put a distinctive, harmless
   marker instruction in `.agents/agents.md` (e.g. "when asked what today's
   test marker is, reply EXACTLY `antigravity-marker-ok`") and ask the agent
   for it in a fresh session. If it does not know the marker, the desktop app
   is not reading this file - stop here, the rest of this adapter is moot.
2. **The hook actually fires.** Try a command this adapter's safety policy
   blocks (see `kernel/safety/safety-policy.md`) and confirm the agent
   reports it was refused, not merely that it chose not to run it. An LLM
   declining on its own judgment is not the same as a deterministic block -
   only the latter is what this adapter claims to provide.
3. **The block actually stops the tool call**, not just prints a message the
   agent then ignores and proceeds anyway.
4. **A benign, ordinary command still works** - confirm the hook is not
   over-blocking (e.g. `ls`, `git status`).

If any of steps 1-3 fail, update `PARITY.md` and `WARNING.md` to reflect what
was actually observed - this whole adapter is written from documentation and
inference, not a live test, and the very first live test's findings
supersede everything written here.

## Local logic test performed for this adapter (does NOT satisfy the above)

A local test confirmed `antigravity_safety_hook.py`'s own Python logic
(payload extraction + calling into `safety_check.py`) works correctly when
fed a hand-built payload shaped like our best guess. **This is a unit test of
the wrapper script in isolation - it proves nothing about whether the real
Antigravity desktop app ever invokes this script, or in what shape it sends
data.** Steps 1-4 above are the real verification; the local test only rules
out "the wrapper is broken even on its own assumptions."
