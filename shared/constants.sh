#!/usr/bin/env bash
# Shared constants — sourced by hooks and utilities across all sub-plugins.
# Mantis conventions: M_-prefixed constants namespace per-engine values.

M_VERSION="0.1.0"
M_STATE_DIR="state"

# M5 sandbox caps (load-bearing — relaxation requires security review per CLAUDE.md contract 2)
M_SANDBOX_RLIMIT_CPU_SEC="${M_SANDBOX_RLIMIT_CPU_SEC:-5}"
M_SANDBOX_RLIMIT_AS_BYTES="${M_SANDBOX_RLIMIT_AS_BYTES:-536870912}"   # 512 MB
M_SANDBOX_RLIMIT_NOFILE="${M_SANDBOX_RLIMIT_NOFILE:-16}"
M_SANDBOX_RLIMIT_FSIZE_BYTES="${M_SANDBOX_RLIMIT_FSIZE_BYTES:-10485760}"  # 10 MB
M_SANDBOX_WALL_CLOCK_SEC="${M_SANDBOX_WALL_CLOCK_SEC:-10}"

# M6 preference floor (no rule dies permanently without /mantis-disable)
M_PREFERENCE_MIN_SURFACE_PROB="${M_PREFERENCE_MIN_SURFACE_PROB:-0.05}"

# M7 rubric thresholds
M_RUBRIC_KAPPA_UNSTABLE="${M_RUBRIC_KAPPA_UNSTABLE:-0.4}"
M_RUBRIC_ESCALATE_DELTA="${M_RUBRIC_ESCALATE_DELTA:-1.5}"

# XDG-compliant global state layout — metrics → STATE, learnings → DATA.
# Spec: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
XDG_STATE_HOME="${XDG_STATE_HOME:-${HOME}/.local/state}"
XDG_DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"

# Generic helpers (plugin-agnostic, safe to keep):

# now_iso — current UTC timestamp in ISO-8601
now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# ensure_dir — create directory if missing, no-op if present
ensure_dir() {
  [[ -d "$1" ]] || mkdir -p "$1"
}

# log — timestamped log to stderr (does not pollute stdout / conversation)
log() {
  printf "[%s] %s\n" "$(now_iso)" "$*" >&2
}
