#!/usr/bin/env python3
"""
Tool-agnostic safety decision core.

Pure block/allow logic shared by every tool adapter (Claude Code, Codex, Cursor,
Antigravity). `check_command` and `check_file_read` are side-effect-free - no I/O,
no exit - so they are import-safe and unit-testable, and every per-tool normalizer
feeds them the same way. Claude Code is the reference implementation.

Command checks run in two layers: (1) the original bypass-detection ported verbatim from
bash-safety-extended.py, and (2) POLICY_DENY - canonical hard-deny command patterns (sudo,
chmod -R, chown, git push --force, git reset --hard, pkill, shutdown, ...) mirrored from
Claude Code's settings.json deny-list, so tools WITHOUT a native deny-list (Cursor,
Antigravity) enforce the FULL policy through this one shared brain. For Claude Code these are
redundant (settings.json denies them first) but harmless. check_file_read likewise blocks
reads of sensitive credential paths (ssh/aws/gnupg/kube/gh/...), not only .env. Deliberately
NOT mirrored: the broad `export` / bare-`eval` denies (too disruptive as universal blocks)
stay Claude-settings-only.

Blocks dangerous patterns that plain deny rules miss:
- two-step download-and-execute, pipe-to-shell, subshell/eval bypasses
- recursive+forced rm hidden in a chained/compound command (deny rules only
  match rm at the start of a command)
- a plain mv that would silently overwrite an existing destination
- reading secret VALUES from env files into the model's context
- reading ssh/aws/gnupg/git-credentials/browser data
- docker host-root mount, --privileged, sensitive host mount
- disk ops on physical devices, fork bombs

Env read policy (narrow, value-focused):
- The threat is secret VALUES entering Claude's context, which only happens when
  a command READS the file into output Claude sees. So we block readers/printers
  (cat/head/grep/cut/source/redirection/`python -c ...read()` ...) targeting a
  protected env file - NOT commands that merely reference it as config
  (`--env-file .env`, `cp .env.example .env`, a commit message that mentions it).
- READABLE exception is `.env.shared` (the soft tier - webhooks, emails, low-risk
  scoped tokens, safe to surface) plus any placeholder file ending in
  .example/.sample/.template/.dist. ALL other env files - `.env`, `.env.local`,
  `.env.production`, ... - are HARD: their VALUES never enter context.
- For any hard env file, `list-env-keys.sh --from <path>` lists key NAMES only
  (add `--classify` for each key's state/kind, still never the value).
"""
import json
import os
import re
import sys

# --- env-file read protection -------------------------------------------------
ENV_TOKEN = re.compile(
    r"""(?:^|[\s'"=:(<>|&;,/])(\.env(?:\.[A-Za-z0-9_-]+)*)(?![\w./-])""",
    re.IGNORECASE,
)
# Soft, readable env file(s) - exact basename match.
ENV_READ_OK_EXACT = {'.env.shared'}
# Placeholder files (carry no secret values) - suffix match, so multi-part names
# like `.env.production.example` or `.env.local.template` are also readable.
ENV_READ_OK_SUFFIX = ('.example', '.sample', '.template', '.dist')
HELPER = 'list-env-keys.sh'


def _env_read_ok(base):
    base = base.lower()
    return base in ENV_READ_OK_EXACT or base.endswith(ENV_READ_OK_SUFFIX)


# Vectors that put a file's CONTENTS into output Claude can read.
ENV_READERS = re.compile(
    r'\b(cat|less|more|head|tail|bat|nl|xxd|od|hexdump|strings|base32|base64'
    r'|grep|egrep|fgrep|rg|ag|awk|sed|cut|tr|sort|uniq|rev|fold|paste|column'
    r'|pr|tac|diff|comm|join|dd)\b',
    re.IGNORECASE,
)
ENV_REDIR = re.compile(r'<\s*\.env|\$\(\s*<', re.IGNORECASE)          # `< .env` or `$(< ...)`
ENV_SOURCE = re.compile(r'^\s*(?:source|\.)\s', re.IGNORECASE)        # `source .env` / `. ./.env`
ENV_INTERP = re.compile(r'\b(python3?|perl|ruby|node|deno|php)\b[^|;&]*\s-(?:c|e|p|n|r)\b', re.IGNORECASE)


def _reads_into_context(seg):
    return bool(
        ENV_READERS.search(seg) or ENV_REDIR.search(seg)
        or ENV_SOURCE.search(seg) or ENV_INTERP.search(seg)
    )


def env_block_reason_bash(command):
    """Block only when a read/print vector targets a protected env file."""
    for seg in re.split(r'&&|\|\||[|;&\n]', command):
        protected = [t for t in ENV_TOKEN.findall(seg) if not _env_read_ok(t)]
        if not protected:
            continue
        if HELPER in seg:
            continue
        if not _reads_into_context(seg):
            continue  # references the file as config / mention - values never enter context
        return (
            "reading the VALUES of a protected env file (%s) into context. Use "
            "`%s --from <path>` for key NAMES only (add --classify for state), or "
            "`.env.shared` for soft values safe to surface. Passing it as config "
            "(e.g. `--env-file`) is fine." % (protected[0], HELPER)
        )
    return None


def rm_recursive_force(command):
    """True if ANY segment invokes rm with BOTH a recursive and a force flag.

    Defense-in-depth beyond the deny rules: a permission rule like `rm -rf *` only
    matches rm at the START of a command, so a chained/embedded form such as
    `cd build && rm -rf .` slips past it. This inspects every shell segment and
    checks the flags on the rm invocation itself (short bundles per-letter, long
    flags by exact name), so it does not false-positive on another command's flags.
    """
    for seg in re.split(r'&&|\|\||[|;&\n]', command):
        m = re.match(r'\s*(?:\w+=\S+\s+)*(?:command\s+|\\)?rm\b(.*)', seg, re.IGNORECASE)
        if not m:
            continue
        has_r = has_f = False
        for tok in re.findall(r'(?<!\S)--?[A-Za-z][A-Za-z-]*', m.group(1)):
            if tok.startswith('--'):
                has_r = has_r or tok == '--recursive'
                has_f = has_f or tok == '--force'
            else:  # short bundle like -rf / -r / -fr
                has_r = has_r or 'r' in tok or 'R' in tok
                has_f = has_f or 'f' in tok or 'F' in tok
        if has_r and has_f:
            return True
    return False


def mv_overwrite_target(command):
    """Return the existing destination a plain `mv` would silently overwrite, else None.

    Migration-safety guard: `mv a b` where b already exists destroys b with no warning.
    Best-effort - skips globs/quotes/vars/flags so it does not misfire on dynamic paths.
    """
    for seg in re.split(r'&&|\|\||[|;&\n]', command):
        m = re.match(r'\s*(?:\w+=\S+\s+)*mv\b(.*)', seg, re.IGNORECASE)
        if not m:
            continue
        args = m.group(1).strip()
        if not args or any(c in args for c in '*?"\'$`~[]{}'):
            continue  # too dynamic to reason about safely
        parts = [p for p in args.split() if not p.startswith('-')]
        if len(parts) < 2:
            continue
        dest = parts[-1]
        for src in parts[:-1]:
            target = os.path.join(dest, os.path.basename(src.rstrip('/'))) if os.path.isdir(dest) else dest
            try:
                if os.path.lexists(target) and os.path.abspath(target) != os.path.abspath(src):
                    return target
            except OSError:
                continue
    return None


DANGEROUS = [
    (r'(curl|wget)\s+[^|;&]*\s*(-o\s*\S+|>\s*\S+).*(?:&&|;|\|\|).*\b(bash|sh|zsh)\b\s+\S+',
     'two-step download-then-execute (curl/wget to file, then exec)'),
    (r'(curl|wget)[^|]+\|\s*(bash|sh|zsh|fish)\b',
     'piping curl/wget directly to shell'),
    (r'\b(bash|sh|zsh)\s+-c\s+["\'][^"\']*\b(rm\s+-[a-zA-Z]*[rf]|curl|wget|chmod\s+(?:777|666|\+s)|sudo)\b',
     'subshell -c bypass with destructive command'),
    (r'\beval\s+["\'][^"\']*\b(rm\s+-[a-zA-Z]*[rf]|curl|wget|chmod\s+(?:777|666|\+s)|sudo)\b',
     'eval bypass with destructive command'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od)\s+[^|;&]*\.ssh/(id_|authorized_keys|known_hosts)',
     'reading SSH keys/config via bash'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od)\s+[^|;&]*\.aws/credentials',
     'reading AWS credentials via bash'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od)\s+[^|;&]*\.gnupg/',
     'reading GPG keyring via bash'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od)\s+[^|;&]*\.git-credentials\b',
     'reading git credentials via bash'),
    (r'\bdd\s+(if|of)=/dev/(disk|sd[a-z]|nvme|hd[a-z])',
     'dd targeting physical disk device'),
    (r'\bmkfs\.[a-z0-9]+\s+/dev/',
     'filesystem format on device'),
    (r'\bfdisk\s+/dev/',
     'fdisk on device'),
    (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:',
     'fork bomb'),
    (r'docker\s+run\s+[^#\n]*-v\s+/:(\s|/)',
     'docker mounting host root filesystem'),
    (r'docker\s+run\s+[^#\n]*--privileged\b',
     'docker --privileged flag'),
    (r'docker\s+(run|create)\s+[^#\n]*-v\s+\S*(\.ssh|\.aws|\.gnupg|\.kube|\.docker|\.config/gh)\b',
     'docker mounting a sensitive host path (ssh/aws/gnupg/kube/docker/gh)'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od|grep|egrep|fgrep|rg|ag|sqlite3)\s+[^|;&]*Library/(Cookies|Safari|Application Support/Google/Chrome|Application Support/Chromium|Application Support/Firefox|Application Support/BraveSoftware|Application Support/Microsoft Edge|Application Support/Arc)/',
     'reading browser data (cookies/history/sessions) via bash'),
    (r'\b(cat|less|more|head|tail|bat|nl|xxd|od|grep|egrep|fgrep|rg|ag|sqlite3)\s+[^|;&]*\.(mozilla|config/google-chrome|config/chromium)/',
     'reading browser data on Linux via bash'),
    (r'\bpython3?\s+-c\s+["\'][^"\']*\b(os\.system|subprocess\.|shutil\.rmtree|os\.remove|os\.unlink|os\.rmdir|os\.path\.expanduser.*\.(ssh|aws|gnupg))',
     'python -c bypass invoking shell or touching sensitive paths'),
]


# Canonical hard-deny command patterns, mirrored from kernel/settings.json's `deny` array.
# Matched CASE-SENSITIVELY (unlike DANGEROUS): command flags are case-sensitive, so `-D`
# (force-delete) must not also catch the safe `-d`, nor `-R` catch `-r`. For Claude Code these
# are redundant with the settings.json deny; they exist here so Cursor / Antigravity - which
# have no native deny-list - enforce the same hard blocks through the shared hook. Not mirrored:
# the broad `export` / bare-`eval` denies (too disruptive as a universal block).
POLICY_DENY = [
    (r'\bmv\s+-[A-Za-z]*f', 'forced mv (-f) can silently overwrite the destination'),
    (r'\bsudo\b', 'sudo - privilege escalation is blocked'),
    (r'\bchmod\s+(-[A-Za-z]*R|777|666|\+s)', 'chmod recursive / world-writable / setuid'),
    (r'\bchown\b', 'chown - ownership change is blocked'),
    (r'\bmkfs(\.[a-z0-9]+)?\b', 'mkfs - filesystem creation is blocked'),
    (r'\bdd\s+(if|of)=', 'dd raw disk read/write (if=/of=)'),
    (r'\blaunchctl\b', 'launchctl - macOS service control is blocked'),
    (r'\bgit\s+push\b[^|;&]*\s(--force|-f)\b', 'git push --force is blocked'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard discards work; run it yourself if intended'),
    (r'\bgit\s+clean\s+-[A-Za-z]*[fd]', 'git clean -f/-d deletes untracked files'),
    (r'\bgit\s+branch\s+-D\b', 'git branch -D force-deletes a branch'),
    (r'\bgit\s+commit\b[^|;&]*--no-verify', 'git commit --no-verify bypasses pre-commit hooks'),
    (r'\bnpm\s+publish\b', 'npm publish is blocked'),
    (r'\bnpm\s+(install|i)\b[^|;&]*\s(-g\b|--global\b)', 'npm global install is blocked'),
    (r'\bpkill\b', 'pkill - bulk process kill is blocked'),
    (r'\b(shutdown|reboot|halt)\b', 'system shutdown/reboot/halt is blocked'),
]

# Sensitive file paths whose CONTENTS must never enter the model's context, mirrored from
# Claude Code's settings.json Read() denies. check_file_read blocks a native read tool from
# opening these (the DANGEROUS list already covers the main ones read via a bash command).
SENSITIVE_READ = [
    (r'/\.ssh/', 'SSH keys / config'),
    (r'/\.gnupg/', 'GPG keyring'),
    (r'/\.aws/', 'AWS credentials'),
    (r'/\.azure/', 'Azure credentials'),
    (r'/\.kube/', 'Kubernetes config'),
    (r'/\.config/gh/', 'GitHub CLI credentials'),
    (r'\.git-credentials(?:\b|$)', 'git credentials'),
    (r'/\.docker/config\.json(?:\b|$)', 'docker registry credentials'),
    (r'/\.npmrc(?:\b|$)', 'npm credentials'),
    (r'/\.pypirc(?:\b|$)', 'PyPI credentials'),
    (r'/Library/Keychains/', 'macOS keychain'),
    (r'/Library/(Cookies|Safari)/', 'browser data'),
    (r'/Library/Application Support/(Google/Chrome|Chromium|Firefox|BraveSoftware|Microsoft Edge|Arc)/', 'browser data'),
    (r'/\.(mozilla|config/google-chrome|config/chromium)/', 'browser data'),
    (r'/Hesla', 'a passwords file'),
]


def check_command(command):
    """Pure decision: return a block reason for an unsafe shell command, else None.

    Composes the same four checks the Claude Code hook applied inline, in the same
    order, so behavior is identical. No I/O, no exit - safe to import and unit-test,
    and callable by every tool adapter.
    """
    if not command:
        return None

    reason = env_block_reason_bash(command)
    if reason:
        return reason

    if rm_recursive_force(command):
        return (
            "recursive + forced rm in a chained/compound command. The deny rules "
            "only catch rm at the start of a command; this catches it anywhere. "
            "If you must delete recursively, ask the user to run it themselves."
        )

    mv_target = mv_overwrite_target(command)
    if mv_target:
        return (
            "this mv would silently overwrite an existing path (%s). Verify it, then "
            "move/rename deliberately - or remove the existing target yourself first."
            % mv_target
        )

    for pattern, why in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            return why

    for pattern, why in POLICY_DENY:
        if re.search(pattern, command):  # case-sensitive: -D vs -d, -R vs -r differ
            return why

    return None


def check_file_read(file_path):
    """Pure decision: block reading a secret file's values, else None.

    Two tiers: (1) sensitive credential paths (ssh/aws/gnupg/kube/gh/keychains/browser
    data/...) mirrored from Claude Code's settings.json Read() denies, blocked outright;
    (2) .env / .env.* hard-protected except the soft .env.shared and placeholder
    (.example/.sample/.template/.dist) files. Any other path is allowed.
    """
    if not file_path:
        return None

    for pattern, label in SENSITIVE_READ:
        if re.search(pattern, file_path):
            return (
                "reading %s is blocked - these secrets must never enter the model's "
                "context." % label
            )

    base = os.path.basename(file_path).lower()
    if base == ".env" or base.startswith(".env."):
        if _env_read_ok(base):
            return None
        return (
            "reading a protected env file (%s) - use `%s --from %s` for key NAMES only "
            "(add --classify for state), or read `.env.shared`."
            % (os.path.basename(file_path), HELPER, file_path)
        )
    return None


def normalize_claude(data):
    """Claude Code hook JSON -> ('command', cmd) | ('read', path) | None."""
    tool = data.get("tool_name")
    tool_input = data.get("tool_input", {}) or {}
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        return ("command", cmd) if cmd else None
    if tool == "Read":
        fp = tool_input.get("file_path", "") or ""
        return ("read", fp) if fp else None
    return None


NORMALIZERS = {
    "claude": normalize_claude,
    # later plans register: "codex", "cursor", "antigravity"
}


def emit_block(tool, reason, command=None):
    """Write the tool-appropriate block signal and exit non-zero."""
    if tool == "cursor":
        # Cursor hooks read a JSON verdict on stdout (added in the Cursor adapter plan).
        print(json.dumps({"permission": "deny", "user_message": reason}))
        sys.exit(0)
    # Claude Code + Codex: stderr message + exit code 2.
    print(f"BLOCKED by safety hook: {reason}", file=sys.stderr)
    if command:
        print(f"Command: {command}", file=sys.stderr)
    print("This is a hard safety boundary. Do NOT retry with a workaround.", file=sys.stderr)
    sys.exit(2)


def _parse_tool_arg(argv):
    if "--tool" in argv:
        i = argv.index("--tool")
        if i + 1 < len(argv):
            return argv[i + 1]
    return "claude"


def main():
    tool = _parse_tool_arg(sys.argv)
    normalize = NORMALIZERS.get(tool, normalize_claude)
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    norm = normalize(data)
    if norm is None:
        sys.exit(0)
    kind, payload = norm

    reason = check_command(payload) if kind == "command" else check_file_read(payload)
    if reason:
        emit_block(tool, reason, payload if kind == "command" else None)
    sys.exit(0)


if __name__ == "__main__":
    main()
