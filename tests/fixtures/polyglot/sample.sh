#!/usr/bin/env bash
# Polyglot fixture — SC2086 unquoted variable expansion.
# `$files` expands unquoted on line 10; any whitespace or glob char splits wrong.
# Parses clean (bash does not reject this); shellcheck SC2086 would flag line 10.

set -uo pipefail

files="foo bar baz"

for f in $files; do
    echo "processing $f"
done
