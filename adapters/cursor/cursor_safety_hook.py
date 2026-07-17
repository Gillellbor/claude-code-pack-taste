#!/usr/bin/env python3
"""
Cursor hook wrapper for the tool-agnostic safety core.

Wires Cursor's `beforeShellExecution` and `beforeReadFile` agent hooks (see
`.cursor/hooks.json` in this same adapter dir) to the shared decision core,
`kernel/safety/safety_check.py`. Self-contained, stdlib only - Cursor invokes
this script directly as a subprocess, so it cannot assume any package beyond
what ships with the host's Python.

Shared-core resolution order (first match wins):
1. `PACK_SAFETY_DIR` env var, if set and it contains `safety_check.py`.
2. `~/.cursor/safety` - the bootstrap's default install location for this
   adapter (mirrors Claude Code's `~/.claude/safety`).
3. `~/.claude/safety` - fallback for a machine where only Claude Code's half
   of the pack is installed but Cursor is being wired up against it too.
4. `<this file>/../../kernel/safety` - repo-relative, so this script also
   runs straight out of a checked-out pack repo (e.g. for adapter
   verification) before any bootstrap install has happened.

Cursor hook contract (cursor.com/docs/agent/hooks, verified 2026-07-14):
- `beforeShellExecution` stdin: {"command": "...", "cwd": "...",
  "hook_event_name": "beforeShellExecution", ...}. Output:
  {"permission": "allow"|"deny"|"ask", "user_message": "...",
  "agent_message": "..."}.
- `beforeReadFile` stdin: {"file_path": "...", "content": "...",
  "hook_event_name": "beforeReadFile", ...}. Output:
  {"permission": "allow"|"deny", "user_message": "..."}.
- The shared core only ever decides allow/deny (no "ask" tier - see PARITY.md),
  so this wrapper never emits "ask".

Fail-open by design: any missing shared core, malformed stdin, or unexpected
crash falls through to ALLOW, matching safety_check.py's own posture on bad
input (see its main(): a JSON parse failure there also exits 0/allow). The
block logic is the safety boundary; the wrapper itself is not meant to be a
second, independent thing that can also fail shut. `hooks.json` sets
`failClosed: true` at the Cursor level instead, since Cursor - unlike Claude
Code - has no native deterministic deny-list as a second layer if this hook
never runs at all (see PARITY.md).
"""
import json
import os
import sys


def _resolve_safety_dir():
    """Return the directory holding safety_check.py, or None if not found."""
    env_dir = os.environ.get("PACK_SAFETY_DIR")
    if env_dir and os.path.isfile(os.path.join(env_dir, "safety_check.py")):
        return env_dir

    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.expanduser("~/.cursor/safety"),
        os.path.expanduser("~/.claude/safety"),
        os.path.normpath(os.path.join(here, "..", "..", "kernel", "safety")),
    ]
    for candidate in candidates:
        if os.path.isfile(os.path.join(candidate, "safety_check.py")):
            return candidate
    return None


def _load_stdin_json():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None


def _allow():
    print(json.dumps({"permission": "allow"}))
    sys.exit(0)


def main():
    safety_dir = _resolve_safety_dir()
    if not safety_dir:
        # Shared core not found on this machine - fail open rather than break
        # every shell command / file read in the editor.
        _allow()
        return

    sys.path.insert(0, safety_dir)
    try:
        import safety_check
    except ImportError:
        _allow()
        return

    data = _load_stdin_json()
    if data is None:
        _allow()
        return

    event = data.get("hook_event_name", "")

    if event == "beforeShellExecution":
        # mv_overwrite_target() in the shared core stats real paths on disk,
        # so the check must run from the command's actual working directory,
        # not whatever cwd this subprocess happened to inherit from Cursor.
        cwd = data.get("cwd")
        if cwd and os.path.isdir(cwd):
            try:
                os.chdir(cwd)
            except OSError:
                pass
        reason = safety_check.check_command(data.get("command", "") or "")
    elif event == "beforeReadFile":
        reason = safety_check.check_file_read(data.get("file_path", "") or "")
    else:
        # Unknown/future event wired to this script by mistake - fail open.
        reason = None

    if reason:
        # Mirrors safety_check.emit_block()'s own "cursor" branch verbatim -
        # reused directly rather than re-encoded here, so this wrapper cannot
        # drift from the shared core's chosen deny shape.
        safety_check.emit_block("cursor", reason)
        return

    _allow()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let an unexpected crash here take down the user's shell
        # command or file read - fail open, same posture as bad-input above.
        _allow()
