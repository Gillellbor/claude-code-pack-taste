---
title: "Codex CLI adapter - install notes"
summary: "Exactly where each Codex adapter file must land at install time, for the bootstrap installer."
status: ai-generated
type: devops
version: "0.1.0"
release: latest
tags: [starter-pack, codex, install, bootstrap, dev-tools]
created: 2026-07-14 00:00
updated: 2026-07-14 00:00
owner: Šimon Hradní
client: ~
path: adapters/codex/install-notes.md
---

# Codex CLI adapter - install notes

For whoever wires `bootstrap/INSTALL.md`'s Codex branch. This is the file-placement map only
- the install FLOW (detect, backup, interview, merge, verify) is `bootstrap/INSTALL.md`'s job
and is described in the design spec, not repeated here.

## File placement map

| Source (this repo) | Destination on the user's machine | Notes |
|---|---|---|
| `kernel/AGENTS.md` | `~/.codex/AGENTS.md` | The canonical behavioral baseline - same content Claude Code reads via its `CLAUDE.md` symlink. Codex also reads a repo-root `AGENTS.md` and every intermediate directory (concatenated, most-specific wins) - that project-level cascade is separate from this global copy and not this adapter's concern. |
| `kernel/safety/safety_check.py` | `~/.codex/safety/safety_check.py` | **Required even if Claude Code is also installed on the same machine.** `codex_safety_hook.py`'s lookup order does check `~/.claude/safety` as a fallback (so a dual-tool machine can share one copy), but a Codex-only install has nothing at that path - always copy it to `~/.codex/safety/` to be safe, do not rely on the fallback. |
| `adapters/codex/codex_safety_hook.py` | `~/.codex/safety/codex_safety_hook.py` | Self-contained, stdlib only - no other files needed alongside it beyond `safety_check.py` in the same directory. |
| `adapters/codex/hooks.json` | `~/.codex/hooks.json` | If the installed Codex version instead reads hooks from `[[hooks.PreToolUse]]` tables inside `config.toml` rather than a standalone `hooks.json` (both forms are documented as existing - see `docs/tool-agnostic-research-2026-07-08.md`), port the same `command` line (`python3 ~/.codex/safety/codex_safety_hook.py`) into that TOML form instead, and skip writing the standalone file. Detect which form the installed Codex version expects before writing either. |
| `adapters/codex/config.toml` | `~/.codex/config.toml` | **Merge, do not blind-overwrite** - the design spec's install flow requires this for every tool. If the user already has a `config.toml`, add/update only the `sandbox_mode`, `approval_policy`, and `[sandbox_workspace_write]` keys this file sets; leave any of the user's own keys (MCP server entries, model choice, etc.) untouched. |
| `adapters/codex/rules/default.rules` | `~/.codex/rules/default.rules` | If the user already has rules files in `~/.codex/rules/`, add this as an additional file rather than replacing an existing one of the same name - Codex is documented to read every `*.rules` file in that directory. |

`adapters/codex/PARITY.md` itself is documentation, not an install artifact - it stays in
the pack repo for reference; it does not need to be copied anywhere on the user's machine.

## Environment variable

`codex_safety_hook.py` honors `PACK_SAFETY_DIR` as its first lookup priority, ahead of
`~/.codex/safety` and `~/.claude/safety`. The installer does not need to set this for a
standard install (the file-placement map above already puts `safety_check.py` where the
hook looks by default) - it exists for non-standard installs (e.g. a shared safety core
kept somewhere else entirely) and for the verification step below.

## Windows note

Codex ships a **native Windows sandbox** (`[windows] sandbox = "elevated" | "unelevated"`
in `config.toml`; WSL1 support was dropped as of Codex 0.115) - unlike the Cursor adapter,
which needs WSL2 for a real OS-level sandbox, Codex does not require WSL on Windows for
`sandbox_mode` to mean anything. `codex_safety_hook.py` is pure Python stdlib, so it runs
identically on native Windows - the only platform-specific detail is the interpreter name
in `hooks.json`'s `command` field: `python3` is not guaranteed to exist on a stock Windows
install (no `python3` alias by default), while `python` or the `py -3` launcher usually is.
The installer should detect the working interpreter command for the target platform and
write that into `hooks.json`'s (or the `config.toml` TOML-hooks form's) `command` string,
rather than hard-coding `python3` universally.

## Verification (before handing off to the user)

Confirm, in this order:

1. `~/.codex/safety/safety_check.py` and `~/.codex/safety/codex_safety_hook.py` both exist
   and `python3 ~/.codex/safety/codex_safety_hook.py` runs without an import error when fed
   `{}` on stdin (should exit 0 - no command/path found, nothing to check).
2. A destructive command payload is blocked: see the Verification section this adapter's
   author ran during development (recorded in the handover report, not duplicated here) -
   repeat it post-install with `PACK_SAFETY_DIR` unset, relying purely on the installed
   `~/.codex/safety/` path, to confirm the real install (not just the repo checkout) works.
3. A safe command payload (e.g. `{"command": ["ls", "-la"]}`) passes (exit 0).
4. `~/.codex/AGENTS.md` is non-empty and matches `kernel/AGENTS.md`'s content.
5. `~/.codex/rules/default.rules` is present and, if `codex execpolicy check` is available
   on the target machine, that it parses without error.

This mirrors the design spec's per-tool verification checklist (blocked command refused;
`AGENTS.md` actually read; skills discoverable; existing config backed up and merged, not
clobbered) - steps 1-3 above are the Codex-specific instantiation of "blocked command
refused."
