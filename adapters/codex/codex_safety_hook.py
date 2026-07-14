#!/usr/bin/env python3
"""
Codex CLI PreToolUse safety hook - Taste starter pack adapter.

Wires the ONE shared safety brain (kernel/safety/safety_check.py, the same core Claude Code
uses) into Codex's hook mechanism, so Codex blocks the same cross-cutting dangers Claude
Code blocks: env-secret-value reads, recursive+forced `rm` anywhere in a chained command,
a `mv` that would silently clobber an existing path, curl|sh / wget|sh, subshell/eval
bypasses, sensitive credential-file reads via bash, dd/mkfs/fdisk-on-device, fork bombs, and
dangerous docker flags. See kernel/safety/safety-policy.md for the full list with reasons,
and adapters/codex/PARITY.md for exactly what this hook does and does not cover for Codex.

Self-contained: stdlib only, no dependency on this repo layout beyond locating
safety_check.py at runtime (see `_find_safety_dir` below).

ASSUMPTIONS ABOUT CODEX'S HOOK JSON (flagged explicitly - Codex's exact PreToolUse payload
schema was not fully published as of the 2026-07-08 research snapshot; see
docs/tool-agnostic-research-2026-07-08.md, "Codex CLI" section, and
https://developers.openai.com/codex/hooks):

  1. One JSON object arrives on stdin per hook invocation. Documented: Codex's hook events
     map ~1:1 to Claude Code's (SessionStart, PreToolUse, PostToolUse, UserPromptSubmit).
  2. For a PreToolUse event wrapping a shell/exec call, the command is assumed to live under
     one of several plausible keys (see COMMAND_PATHS below) and MAY be a single string OR a
     list of argv tokens - Codex's shell tool has historically taken `command: [str, ...]`
     (e.g. ["bash", "-lc", "ls -la"]), not only a single string. Both shapes are handled;
     a list is joined with spaces before being handed to safety_check.check_command, which
     only needs a string to pattern-match against.
  3. For a PreToolUse event wrapping a file-read-like call, the target path is assumed to
     live under one of several plausible keys (see FILE_PATH_PATHS below).
  4. The tool/event name, if present, is read but NOT required to make a decision - this
     hook inspects whatever command/path it can actually find in the payload and lets
     safety_check.py decide, so an unrecognized or renamed event still gets checked rather
     than silently skipped. This is a deliberate robustness choice given the schema is
     unconfirmed, not a claim that the exact field names below are correct.
  5. Codex's documented hook coverage gap applies regardless of anything in this file: it
     does NOT intercept every shell call (the newer `unified_exec` path), nor WebSearch /
     other non-shell tools, and only partially covers edits. This hook cannot compensate for
     a call Codex itself never routes through PreToolUse - see PARITY.md.

Verify these assumptions against a real Codex install before relying on this in production
(e.g. dump a real hook payload to a file and compare against COMMAND_PATHS/FILE_PATH_PATHS
below); update the extraction paths if the real schema differs.
"""
import json
import os
import sys

# Paths Codex's PreToolUse payload might carry a shell command under, checked in order.
# Each entry is a tuple of nested dict keys to walk (see _first_str_or_list).
COMMAND_PATHS = [
    ("command",),
    ("tool_input", "command"),
    ("input", "command"),
    ("arguments", "command"),
    ("params", "command"),
]

# Paths Codex's PreToolUse payload might carry a file-read target path under, checked in
# order, only consulted when no command was found above.
FILE_PATH_PATHS = [
    ("file_path",),
    ("tool_input", "file_path"),
    ("input", "path"),
    ("input", "file_path"),
    ("arguments", "path"),
    ("arguments", "file_path"),
    ("params", "file_path"),
]


def _find_safety_dir():
    """Locate the directory containing safety_check.py, in priority order.

    1. PACK_SAFETY_DIR env var, if the bootstrap installer or the user set one explicitly.
    2. ~/.codex/safety - where the bootstrap installer places a Codex-local copy.
    3. ~/.claude/safety - reuse an already-installed Claude Code pack's shared core, so a
       machine running both tools does not need two copies.
    4. A repo-relative fallback (../../kernel/safety from this file), for running straight
       out of the pack repo before any install step has happened.
    """
    candidates = []
    env_dir = os.environ.get("PACK_SAFETY_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append(os.path.expanduser("~/.codex/safety"))
    candidates.append(os.path.expanduser("~/.claude/safety"))
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.normpath(os.path.join(here, "..", "..", "kernel", "safety")))

    for candidate in candidates:
        if os.path.isfile(os.path.join(candidate, "safety_check.py")):
            return candidate
    return None


def _first_str_or_list(data, paths):
    """Walk each dotted path in `paths` against `data`; return the first non-empty value found."""
    for path in paths:
        node = data
        found = True
        for key in path:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                found = False
                break
        if found and node:
            return node
    return None


def _as_command_string(value):
    """Normalize a command that may be a single string or an argv-token list into one string."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(tok) for tok in value)
    return None


def normalize_codex(data):
    """Codex PreToolUse hook JSON -> ('command', cmd) | ('read', path) | None.

    Command is checked before file path: a shell/exec call is the higher-risk surface, and
    under the ASSUMPTIONS above a payload could plausibly satisfy both extractions.
    """
    if not isinstance(data, dict):
        return None

    raw_command = _first_str_or_list(data, COMMAND_PATHS)
    command = _as_command_string(raw_command)
    if command:
        return ("command", command)

    raw_path = _first_str_or_list(data, FILE_PATH_PATHS)
    if isinstance(raw_path, str) and raw_path:
        return ("read", raw_path)

    return None


def emit_block(reason, command=None):
    """Codex block signal: stderr message + exit code 2.

    Mirrors kernel/safety/safety_check.py's emit_block for the "claude"/"codex" tools -
    same message shape, same exit code - so the two adapters behave identically from the
    human's point of view even though they are wired through different hook mechanisms.
    """
    print(f"BLOCKED by safety hook: {reason}", file=sys.stderr)
    if command:
        print(f"Command: {command}", file=sys.stderr)
    print("This is a hard safety boundary. Do NOT retry with a workaround.", file=sys.stderr)
    sys.exit(2)


def main():
    safety_dir = _find_safety_dir()
    if safety_dir is None:
        # Fail OPEN, loudly, rather than block every single Codex tool call on a broken
        # install. A missing shared brain means the adapter was wired incorrectly - that is
        # an install-time defect to catch at verification (see install-notes.md), not a
        # reason to silently deny all work in every session going forward. The warning is
        # unmissable in Codex's own stderr stream, so it is not a silent failure either way.
        print(
            "codex_safety_hook.py: could not locate safety_check.py (checked "
            "PACK_SAFETY_DIR, ~/.codex/safety, ~/.claude/safety, ../../kernel/safety "
            "relative to this file) - allowing this call by default. Fix the install: see "
            "adapters/codex/install-notes.md.",
            file=sys.stderr,
        )
        sys.exit(0)

    sys.path.insert(0, safety_dir)
    import safety_check  # noqa: E402  (import after sys.path mutation is deliberate)

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # No parseable JSON on stdin - nothing to check against, allow.
        sys.exit(0)

    norm = normalize_codex(data)
    if norm is None:
        sys.exit(0)
    kind, payload = norm

    reason = (
        safety_check.check_command(payload)
        if kind == "command"
        else safety_check.check_file_read(payload)
    )
    if reason:
        emit_block(reason, payload if kind == "command" else None)
    sys.exit(0)


if __name__ == "__main__":
    main()
