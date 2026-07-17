#!/usr/bin/env python3
"""
Antigravity safety hook wrapper - UNVERIFIED, BEST-EFFORT.

Antigravity 2's ".agents/hooks.json" mechanism is "mostly community-documented"
- no confirmed JSON schema from Google as of this writing (see
docs/tool-agnostic-research-2026-07-08.md, Antigravity section). This wrapper
is written against the shape we ASSUME (the closest documented analog, Claude
Code's own PreToolUse hook JSON - Antigravity's own docs are described in that
research as "catching up" to that convention). It has NEVER been confirmed to
run inside the real Antigravity desktop app. Read ../WARNING.md and
../PARITY.md before trusting any of this.

What this does, when it does run:
1. Locates the shared, tool-agnostic safety core (kernel/safety/safety_check.py)
2. Reads one hook-invocation JSON payload from stdin
3. Best-effort extracts a shell command or a file path from that payload -
   the exact field names Antigravity uses are UNCONFIRMED, so this tries
   several plausible key paths (see EXTRACTION ASSUMPTIONS below)
4. Calls the shared check_command() / check_file_read() core - the same
   decision logic Claude Code, Codex, and Cursor all call
5. On a block verdict: prints to stderr and exits 2 (the hard-deny convention
   shared with Claude Code and Codex, via safety_check.emit_block). On no
   verdict, or on input this wrapper cannot parse, it exits 0 (allow) - see
   FAIL-OPEN vs FAIL-CLOSED below for why input-shape ambiguity fails open
   while a MISSING safety core fails closed.

EXTRACTION ASSUMPTIONS (all unconfirmed - adjust once the real payload is seen):
- A shell command may arrive as: tool_input.command (Claude/Codex-style),
  a flat top-level command (Cursor beforeShellExecution-style), params.command,
  input.command, or tool_call.arguments.command (MCP/function-call style).
  First non-empty match wins, in that order.
- A file path may arrive as: tool_input.file_path, a flat top-level file_path,
  a flat top-level path, params.file_path, or input.file_path. Same
  first-match-wins order.
- If a payload carries neither, this hook has nothing to check and allows.
- There is no confirmed way to know which Antigravity "tool" triggered the
  hook (no confirmed tool_name/event field), so this wrapper does not gate on
  tool name at all - it just looks for a command or a path, in that order,
  and checks whichever it finds.

FAIL-OPEN vs FAIL-CLOSED (deliberate, documented choice):
- Malformed / non-JSON stdin -> exit 0 (allow). Mirrors safety_check.py's own
  main(), which does the same on a JSON decode error - this is not a security
  condition, just a hook invoked with input this wrapper cannot parse.
- Safety core NOT FOUND on disk (bad install / missing PACK_SAFETY_DIR) ->
  exit 2 (BLOCK) with a loud stderr message. A missing guardrail is a bigger
  risk than an inconvenient false block, and a broken install should scream,
  not silently run with zero enforcement.
"""
import json
import os
import sys


def resolve_safety_dir():
    """Find kernel/safety/ - env override, then known install homes, then repo-relative.

    Order: $PACK_SAFETY_DIR -> ~/.gemini/safety -> ~/.claude/safety ->
    <this file>/../../kernel/safety (source-tree layout, for running this
    wrapper directly out of the pack repo before any install). Returns the
    first candidate directory that actually contains safety_check.py, or
    None if none do.
    """
    candidates = []
    env_dir = os.environ.get("PACK_SAFETY_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append(os.path.expanduser("~/.gemini/safety"))
    candidates.append(os.path.expanduser("~/.claude/safety"))
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, "..", "..", "kernel", "safety"))

    for candidate in candidates:
        if os.path.isfile(os.path.join(candidate, "safety_check.py")):
            return os.path.abspath(candidate)
    return None


def extract_command(data):
    """Best-effort shell-command extraction. See EXTRACTION ASSUMPTIONS above."""
    lookups = [
        ("tool_input", "command"),
        (None, "command"),
        ("params", "command"),
        ("input", "command"),
    ]
    for parent, key in lookups:
        node = data.get(parent, {}) if parent else data
        if isinstance(node, dict):
            value = node.get(key)
            if value:
                return value

    tool_call = data.get("tool_call")
    if isinstance(tool_call, dict):
        arguments = tool_call.get("arguments")
        if isinstance(arguments, dict):
            value = arguments.get("command")
            if value:
                return value
    return None


def extract_file_path(data):
    """Best-effort file-path extraction. See EXTRACTION ASSUMPTIONS above."""
    lookups = [
        ("tool_input", "file_path"),
        (None, "file_path"),
        (None, "path"),
        ("params", "file_path"),
        ("input", "file_path"),
    ]
    for parent, key in lookups:
        node = data.get(parent, {}) if parent else data
        if isinstance(node, dict):
            value = node.get(key)
            if value:
                return value
    return None


def main():
    safety_dir = resolve_safety_dir()
    if not safety_dir:
        print(
            "BLOCKED by antigravity_safety_hook: cannot locate safety_check.py. "
            "Searched $PACK_SAFETY_DIR, ~/.gemini/safety, ~/.claude/safety, and "
            "the repo-relative kernel/safety/. Fix the install - see "
            "adapters/antigravity/install-notes.md. Failing CLOSED: a missing "
            "safety core is a bigger risk than one blocked command.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.path.insert(0, safety_dir)
    import safety_check  # noqa: E402  (path must be set before this import)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # unparsable input - not a security condition, allow

    if not isinstance(data, dict):
        sys.exit(0)

    command = extract_command(data)
    if command:
        reason = safety_check.check_command(command)
        if reason:
            safety_check.emit_block("antigravity", reason, command)  # exits, never returns
        sys.exit(0)

    file_path = extract_file_path(data)
    if file_path:
        reason = safety_check.check_file_read(file_path)
        if reason:
            safety_check.emit_block("antigravity", reason)  # exits, never returns
        sys.exit(0)

    sys.exit(0)  # nothing recognizable in the payload to check


if __name__ == "__main__":
    main()
