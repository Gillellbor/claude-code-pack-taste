---
title: "Universal install - tool-agnostic Taste pack"
summary: "The single entry point any host agent reads to install the pack into its own tool (Claude Code, Codex, Cursor, Antigravity) on Mac or Windows, configuring itself for its host."
status: draft
type: core
version: "1.0.0"
release: latest
tags: [starter-pack, bootstrap, install, claude-code, codex, cursor, antigravity]
created: 2026-07-17 00:00
updated: 2026-07-17 00:00
owner: Šimon Hradní
client: ~
path: bootstrap/INSTALL.md
---

# Universal install - read this first, whatever tool you are

You are an AI coding agent (Claude Code, Codex, Cursor, Antigravity, or similar) reading this
because the user just dropped this pack into a repo and asked you to set it up. Your job:
detect which tool you are and which OS you are on, then install the pack's shared safety core,
the behavioral baseline, and the adapter for YOUR tool - safely, interactively, confirming
before every change outside the repo.

Claude Code is the canonical implementation; every other tool's config derives from it and
enforces as much of the safety policy as its mechanism allows (each adapter's `PARITY.md`
states exactly what it does and does not cover). You are not expected to be Claude Code - you
are expected to wire YOUR tool to the same shared brain and be honest where it falls short.

## Hard rules for this install session (all tools)

- Do not silently run install commands. Show the command, get approval, then execute.
- Never overwrite an existing config. Back it up first, then merge - never blind-overwrite.
- Never use `rm -rf` during install; use a move-to-backup instead.
- Never use `sudo`. If something needs it, hand the user that one line to run themselves.
- If a step fails, stop. Do not continue to the next step.
- Terse reporting: one line per result. The user can read.

## Step 0 - Identify host tool, OS, shell

**Which tool are you?** Prefer self-knowledge (you usually know your own harness). If unsure,
ask the user: "Installing into Claude Code, Codex, Cursor, or Antigravity?" Route to that
tool's branch below.

**Which OS + shell?**

```bash
uname -s   # Darwin=macOS, Linux=Linux, MINGW/MSYS/CYGWIN=Windows (Git Bash)
```

- macOS / Linux: everything here works as written.
- Windows: **WSL2 is the recommended path** - inside WSL2 this behaves like Linux. Native
  Windows is supported-but-limited (see the Windows section at the bottom): the Python safety
  core runs fine, but the hook `command` lines need `python` or `py -3` instead of `python3`,
  and bash-based kernel hooks need Git Bash. Ask the user which they want before proceeding on
  Windows.

Record the tool, OS, and the working Python interpreter name (`python3` on mac/Linux/WSL2;
detect `python` / `py -3` on native Windows) - you will template it into hook command lines.

## Step 1 - Pre-flight

```bash
for tool in python3 git; do command -v "$tool" >/dev/null 2>&1 && echo "$tool ok" || echo "$tool MISSING"; done
```

`python3` (or `python`/`py -3` on native Windows) and `git` are required. If missing, give the
user OS-specific install commands and stop; do not install system dependencies yourself. Then
confirm the host tool's own binary/app is installed (`claude`, `codex`, Cursor app, Antigravity
app).

## Step 2 - Workspace location interview (shared, all tools)

The pack ships four workspace directories (`_CONTEXT`, `_CLIENTS`, `_BUSINESS`, `_APPS`). Where
they go and what they are named is the user's call - do not assume. This interview is identical
for every tool and is described in full in `../INSTRUCTIONS.md` Step 2 (location options,
optional renaming, conflict check). Follow it there, then return here. The workspace scaffold in
`../workspace/` is tool-neutral: it installs the same way regardless of host tool.

## Step 3 - Back up the host tool's existing config

Before touching the tool's config home, back it up if it exists. Config homes by tool:

| Tool | Config home to back up |
|---|---|
| Claude Code | `~/.claude/` |
| Codex | `~/.codex/` |
| Cursor | `~/.cursor/` and the target project's `.cursor/` |
| Antigravity | `~/.gemini/` and the target workspace's `.agents/` |

```bash
# example, adjust the path per tool:
cp -r ~/.codex ~/.codex.bak-$(date +%Y%m%d-%H%M%S)
```

Report the backup path. If the config home does not exist, say so and skip.

## Step 4 - Install the shared core + behavioral baseline

Two things are common to every tool and must land wherever that tool can reach them:

1. **The shared safety brain** - `kernel/safety/safety_check.py` (plus `safety-policy.md` for
   reference). This is the ONE enforced core. Copy it to the tool's safety dir (see per-tool
   table below). Copy it for EVERY tool even if another tool already has it - do not rely on a
   cross-tool fallback path for a single-tool install.
2. **The behavioral baseline** - `kernel/AGENTS.md`. Place it where the tool reads persistent
   instructions (see per-tool table). Its content is identical across tools; do not fork it.

## Step 5 - Apply YOUR tool's adapter

Each adapter ships pre-built, deterministic files plus an `install-notes.md` with the exact
destination map. Read `adapters/<tool>/install-notes.md` and follow it. Summary of where the
core, baseline, and adapter files land:

### Claude Code (canonical)

Follow the full, battle-tested flow in **`../INSTRUCTIONS.md`** - it already installs the
kernel (`settings.json`, hooks, skills, agents, statusline), places `kernel/safety/` at
`~/.claude/safety/`, and re-creates the `AGENTS.md` <-> `CLAUDE.md` symlink. Nothing to add
here; Claude Code is the reference the others derive from.

### Codex - `adapters/codex/install-notes.md`

| File | Destination |
|---|---|
| `kernel/AGENTS.md` | `~/.codex/AGENTS.md` |
| `kernel/safety/safety_check.py` | `~/.codex/safety/safety_check.py` |
| `adapters/codex/codex_safety_hook.py` | `~/.codex/safety/codex_safety_hook.py` |
| `adapters/codex/hooks.json` | `~/.codex/hooks.json` (or ported into `config.toml` `[[hooks.PreToolUse]]` if that Codex version expects it) |
| `adapters/codex/config.toml` | merge into `~/.codex/config.toml` (only the sandbox/approval keys; keep the user's own) |
| `adapters/codex/rules/default.rules` | `~/.codex/rules/default.rules` (add alongside any existing `*.rules`) |

Codex gets both layers: the shared hook AND its native Rules deny-list. Template the Python
interpreter name into the hook `command` per Step 0.

### Cursor - `adapters/cursor/install-notes.md`

| File | Destination |
|---|---|
| `kernel/safety/safety_check.py` | `~/.cursor/safety/safety_check.py` |
| `adapters/cursor/cursor_safety_hook.py` | `~/.cursor/safety/cursor_safety_hook.py` |
| `adapters/cursor/hooks.json` | `~/.cursor/hooks.json` (user-level) |
| `adapters/cursor/rules/pack-baseline.mdc` | `<project>/.cursor/rules/pack-baseline.mdc` (per project) |
| `adapters/cursor/sandbox.json` | `<project>/.cursor/sandbox.json` or `~/.cursor/sandbox.json` (optional OS jail) |
| `kernel/AGENTS.md` | `<project>/AGENTS.md` (Cursor reads it natively at project root; Cursor has NO home-dir global rules file) |

The Cursor hook is the ONLY deterministic deny layer (`failClosed: true` is deliberate - do not
change it). Resolve `~` in the hook `command` to an absolute path if a real Cursor install does
not expand it.

### Antigravity - STOP, read `adapters/antigravity/WARNING.md` first

Before writing anything for Antigravity, surface `adapters/antigravity/WARNING.md` to the user
and require explicit acknowledgement (see Step 7). This adapter is best-effort and unverified.
Destinations (all low-confidence, per `install-notes.md`):

| File | Assumed destination |
|---|---|
| `kernel/AGENTS.md` content | `<workspace>/.agents/agents.md` |
| `adapters/antigravity/hooks.json` | `<workspace>/.agents/hooks.json` |
| `adapters/antigravity/antigravity_safety_hook.py` + `kernel/safety/safety_check.py` | `~/.gemini/safety/` |

`~/.gemini/GEMINI.md` collides with the Gemini CLI's global file - check and back up before
touching `~/.gemini/`.

## Step 6 - Merge, never clobber (all tools)

If the user already had a config for this tool (Step 3 found one), do NOT replace it wholesale.
Read their existing config, compare against what this pack ships, and present an area-by-area
recommendation (what of theirs to keep, what the pack adds, where they conflict). Write the
agreed merged result explicitly. The backup from Step 3 protects the original regardless.

## Step 7 - Antigravity acknowledgement gate (Antigravity only)

Do not write a single Antigravity file until the user has read `adapters/antigravity/WARNING.md`
and explicitly typed acknowledgement. The load-bearing facts they must confirm they understand:
the desktop app is NOT confirmed to read these files at all; Antigravity has documented,
unresolved prompt-injection / data-exfiltration / RCE issues; do NOT use it on client data
without the separate enterprise Gemini Cloud platform. If they do not acknowledge, skip
Antigravity entirely and tell them it was skipped.

## Step 8 - Verify (per tool)

Each adapter's `install-notes.md` has a verification section. The universal checks:

1. **A blocked command is refused.** Feed the tool's hook a destructive payload (e.g. a chained
   `rm -rf`) and confirm it is blocked, not run. For Antigravity, this means the 4-step hands-on
   protocol in `install-notes.md` - a local wrapper test is NOT sufficient proof the app honors it.
2. **The behavioral baseline is actually read.** Ask the agent something stated only in
   `AGENTS.md` and confirm it reflects that content.
3. **Existing config was backed up and merged, not clobbered.**

## Step 9 - Hand off

Tell the user what was installed, where, and the backup path. Point them at their tool's
`adapters/<tool>/PARITY.md` so they know exactly what is and is not enforced for their tool.
The pack repo can now be deleted - everything lives in the tool's config home and the workspace.

---

## Windows (all tools)

- **WSL2 = recommended.** Inside WSL2 every tool behaves like Linux; nothing special.
- **Native Windows = supported-but-limited:**
  - `safety_check.py` and every adapter wrapper are pure Python stdlib and run natively.
  - Hook `command` lines: substitute `python` or `py -3` for `python3` (native Windows has no
    `python3` alias by default). Detect the working interpreter in Step 0 and template it in.
  - Bash-based kernel hooks (`notes-research.sh`, `inject-current-time.sh`, `statusline.sh`,
    Claude Code only) need Git Bash or a rewrite; flag this to the user.
  - Sandbox strength differs: Codex has a native Windows sandbox; Cursor's real sandbox needs
    WSL2; the Python hook layer is identical everywhere.

## Bottom line

One pack, one shared safety brain, one behavioral baseline - installed into whichever tool you
are, wired through that tool's own hook mechanism, honest via `PARITY.md` about what each tool
cannot enforce. Claude Code is the reference; the rest derive from it and degrade transparently.
