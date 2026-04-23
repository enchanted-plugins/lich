#!/usr/bin/env bash
# Lich canonical hook dispatcher (v1)
#
# Contract: advisory-only, fail-open. Always exits 0 regardless of outcome.
# Invoked by per-plugin wrappers at plugins/<name>/hooks/dispatch.sh, which
# simply delegate here with the same argv. The plugin's hooks.json supplies
# the command name as $1 (e.g. "lich-analyze", "lich-sandbox").
#
# Stdin: PostToolUse JSON payload from Claude Code (tool_name, tool_input, ...).
# Stdout: nothing (polluting the conversation context is banned by
#         shared/conduct/hooks.md § Logging).
# Stderr: nothing user-visible; errors are swallowed per fail-open contract.
# Side effects: may spawn one background analysis process; appends to a log file.
#
# Performance budget: < 100ms synchronous. Heavy work is backgrounded.

set -uo pipefail   # deliberately NO -e: fail-open

# ---------------------------------------------------------------------------
# Subagent guard — prevent hook recursion inside spawned subagents.
# See shared/conduct/hooks.md § Subagent-loop guard.
# ---------------------------------------------------------------------------
if [[ -n "${CLAUDE_SUBAGENT:-}" ]]; then
    exit 0
fi

COMMAND="${1:-}"
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# ---------------------------------------------------------------------------
# Repo-root detection: walk up from $CLAUDE_PLUGIN_ROOT (or this script's dir)
# until we find a .git directory. Fail-open if none.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null)" || SCRIPT_DIR=""
START_DIR="${CLAUDE_PLUGIN_ROOT:-$SCRIPT_DIR}"
REPO_ROOT=""
_cur="$START_DIR"
while [[ -n "$_cur" && "$_cur" != "/" ]]; do
    if [[ -d "$_cur/.git" ]]; then
        REPO_ROOT="$_cur"
        break
    fi
    _parent="$(dirname "$_cur")"
    [[ "$_parent" == "$_cur" ]] && break
    _cur="$_parent"
done

# ---------------------------------------------------------------------------
# Log path resolution: prefer repo-local .claude/logs/hooks.log; fall back to
# $TMPDIR (or /tmp) on read-only / missing repo-root. mkdir -p parent.
# ---------------------------------------------------------------------------
LOG=""
if [[ -n "$REPO_ROOT" ]]; then
    _log_dir="$REPO_ROOT/.claude/logs"
    mkdir -p "$_log_dir" 2>/dev/null && touch "$_log_dir/hooks.log" 2>/dev/null && LOG="$_log_dir/hooks.log"
fi
if [[ -z "$LOG" ]]; then
    _tmp="${TMPDIR:-/tmp}"
    mkdir -p "$_tmp" 2>/dev/null
    LOG="$_tmp/lich-hooks.log"
    touch "$LOG" 2>/dev/null || LOG="/dev/null"
fi

_log() {
    # one-line entries, greppable. Never emit to stdout.
    echo "[$(date -Is 2>/dev/null || date)] lich-dispatch cmd=$COMMAND $*" >> "$LOG" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# jq graceful degradation: if jq not in PATH, we cannot parse the payload.
# Log and exit 0.
# ---------------------------------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    _log "skip:no-jq"
    exit 0
fi

# ---------------------------------------------------------------------------
# Parse stdin payload once. If stdin is empty or not JSON, degrade to empty
# values — the command handlers will decide whether that's a skip.
# ---------------------------------------------------------------------------
PAYLOAD="$(cat 2>/dev/null || true)"
TOOL_NAME=""
FILE_PATH=""
if [[ -n "$PAYLOAD" ]]; then
    # Single jq invocation — emits two tab-separated values. Parsing via bash
    # read avoids a second jq/sed fork, which matters on Windows git-bash
    # where each fork-exec costs ~150ms. Strip trailing CR (\r) because jq
    # on Windows git-bash emits CRLF line endings which would break the
    # *.py glob match below.
    IFS=$'\t' read -r TOOL_NAME FILE_PATH < <(printf '%s' "$PAYLOAD" | jq -r '[.tool_name // "", .tool_input.file_path // ""] | @tsv' 2>/dev/null) || true
    TOOL_NAME="${TOOL_NAME%$'\r'}"
    FILE_PATH="${FILE_PATH%$'\r'}"
fi

# ---------------------------------------------------------------------------
# File-extension gate: v1 runtime is Python-only. Non-.py paths are skipped
# with an honest log line. An empty file_path is also a skip (no target to
# analyze).
# ---------------------------------------------------------------------------
_is_python_file() {
    [[ "${1,,}" == *.py ]]
}

# ---------------------------------------------------------------------------
# Command switch.
# ---------------------------------------------------------------------------
case "$COMMAND" in
    lich-analyze)
        if [[ -z "$FILE_PATH" ]]; then
            _log "skip:no-file-path tool=$TOOL_NAME"
            exit 0
        fi
        if ! _is_python_file "$FILE_PATH"; then
            _log "skip:non-py file=$FILE_PATH"
            exit 0
        fi
        if [[ -z "$REPO_ROOT" ]]; then
            _log "skip:no-repo-root"
            exit 0
        fi
        _script="$REPO_ROOT/plugins/lich-core/scripts/__main__.py"
        _log "spawn lich-core file=$FILE_PATH"
        # Background spawn keeps us inside the synchronous budget. All three
        # fds are redirected; `disown` detaches from the job table so the
        # child survives the parent shell's exit. On Windows git-bash,
        # `nohup` adds ~300ms fork overhead without benefit here — fd
        # redirection + disown is sufficient.
        # If the target script does not exist yet (Agent 2's territory), the
        # python invocation will fail and log — that's fail-open by design.
        python "$_script" "$FILE_PATH" >> "$LOG" 2>&1 </dev/null &
        disown 2>/dev/null || true
        exit 0
        ;;
    lich-sandbox)
        if [[ -z "$FILE_PATH" ]]; then
            _log "skip:no-file-path tool=$TOOL_NAME"
            exit 0
        fi
        if ! _is_python_file "$FILE_PATH"; then
            _log "skip:non-py file=$FILE_PATH"
            exit 0
        fi
        if [[ -z "$REPO_ROOT" ]]; then
            _log "skip:no-repo-root"
            exit 0
        fi
        _script="$REPO_ROOT/plugins/lich-sandbox/scripts/sandbox.py"
        _log "spawn lich-sandbox file=$FILE_PATH"
        # sandbox.py's argv[1] is the review-flags.jsonl path, not a source
        # file. Omit the positional arg so it uses its default input
        # (plugins/lich-core/state/review-flags.jsonl).
        python "$_script" >> "$LOG" 2>&1 </dev/null &
        disown 2>/dev/null || true
        exit 0
        ;;
    lich-verdict-compose)
        if [[ -z "$REPO_ROOT" ]]; then
            _log "skip:no-repo-root"
            exit 0
        fi
        # Gate only on populated non-Python FILE_PATH. Stop-event invocations
        # arrive with empty FILE_PATH and must still compose over all recent
        # verdicts.
        if [[ -n "$FILE_PATH" ]] && ! _is_python_file "$FILE_PATH"; then
            _log "skip:non-py file=$FILE_PATH cmd=lich-verdict-compose"
            exit 0
        fi
        _script="$REPO_ROOT/plugins/lich-verdict/scripts/compose.py"
        _log "spawn lich-verdict-compose file=$FILE_PATH"
        _args=()
        if [[ -n "$FILE_PATH" ]]; then
            _args=(--file "$FILE_PATH")
        fi
        python "$_script" "${_args[@]}" >> "$LOG" 2>&1 </dev/null &
        disown 2>/dev/null || true
        exit 0
        ;;
    lich-preference-update)
        # PostToolUse: after M1/M5 have written state, scan review-flags.jsonl
        # and update surfaced.jsonl with Thompson-sampled surfacing decisions.
        # The 5% floor is enforced inside posteriors.py — we never clamp to 0.
        if [[ -z "$REPO_ROOT" ]]; then
            _log "skip:no-repo-root"
            exit 0
        fi
        # Non-Python file_path: still safe to scan (flags are language-agnostic
        # at this layer), but skip for consistency with other engines unless
        # the invocation is a Stop-event (empty FILE_PATH).
        if [[ -n "$FILE_PATH" ]] && ! _is_python_file "$FILE_PATH"; then
            _log "skip:non-py file=$FILE_PATH cmd=lich-preference-update"
            exit 0
        fi
        _script="$REPO_ROOT/plugins/lich-preference/scripts/observer.py"
        if [[ ! -f "$_script" ]]; then
            _log "skip:missing-script $_script"
            exit 0
        fi
        _log "spawn lich-preference-update file=$FILE_PATH"
        # Background spawn — observer.py's --scan-flags reads M1 output and
        # appends one snapshot line to surfaced.jsonl. Fail-open: if the
        # python invocation errors, it logs but does not block the hook.
        python "$_script" --scan-flags >> "$LOG" 2>&1 </dev/null &
        disown 2>/dev/null || true
        exit 0
        ;;
    lich-judge)
        # M7 rubric judgment is a Claude-in-loop Sonnet subagent; hooks run in
        # a plain subprocess and cannot spawn LLM calls. Honest no-op marker —
        # do NOT silently pretend M7 ran (per CLAUDE.md anti-pattern "Bare M7
        # score without Kappa" and the verdict bar's honest-numbers contract).
        # Future: when a Claude-API batch-judge path lands, fire it here.
        _log "NOTE:lich-judge-noop reason=llm-judge-is-claude-in-loop file=$FILE_PATH"
        exit 0
        ;;
    *)
        # Phase 2 stubs land here (preference, rubric, verdict, python, typescript).
        # Honest NOTE, fail-open.
        _log "NOTE:unknown-command tool=$TOOL_NAME file=$FILE_PATH"
        exit 0
        ;;
esac
