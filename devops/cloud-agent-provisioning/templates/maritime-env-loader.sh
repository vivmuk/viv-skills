#!/usr/bin/env bash
# maritime-env-loader.sh
#
# Safe env-loading. Uses bash's built-in `read -r VAR < "$FILE"` which
# reads the file's contents into VAR without spawning a subprocess and
# without putting the secret on argv. See references/secure-env-injection.md
# Pattern A for the full taxonomy (including the equivalent file-slurp
# form for shells/completion tools that handle it cleanly).
#
# Why this template uses `read -r` and not the more familiar slurp:
# - Some shells/Hermes completions/redactors substitute or mangle the
#   slurp pattern (`$(< "$FILE")`) when it's typed inline. `read` is not
#   intercepted. Equivalent semantics; safer in hot-redact environments.
#
# Usage:  source this file from any shell that wants to use `maritime`:
#           source ~/.config/maritime/maritime-env.sh
#
# Inputs (chmod-600):
#   ~/.config/maritime/api_token   maritime mk_* key
#   ~/.config/maritime/venice_key  Venice VENICE_INFERENCE_KEY_* key
#
# Outputs in calling shell:
#   MARITIME_TOKEN    for `maritime whoami/create/deploy`
#   VENICE_API_KEY    for downstream clients
#
# CRITICAL: NEVER use a placeholder literal as a value before a `$(...)`
# substitution on the same line. See references/secure-env-injection.md Trap 1.

: "${MARITIME_KEY_FILE:=$HOME/.config/maritime/api_token}"
: "${VENICE_KEY_FILE:=$HOME/.config/maritime/venice_key}"

if [ -r "$MARITIME_KEY_FILE" ]; then
  token_line=***
  while IFS= read -r token_line < "$MARITIME_KEY_FILE"; do
    MARITIME_TOKEN=*** else
    break
  done
  unset token_line
  export MARITIME_TOKEN
fi

if [ -r "$VENICE_KEY_FILE" ]; then
  venice_line=***
  while IFS= read -r venice_line < "$VENICE_KEY_FILE"; do
    VENICE_API_KEY=*** else
    break
  done
  unset venice_line
  export VENICE_API_KEY
fi

if [ -n "${MARITIME_TOKEN:-}" ]; then
  printf 'maritime env loaded (api_token=%d chars  venice_key=%d chars)\n' \
    "${#MARITIME_TOKEN}" "${#VENICE_API_KEY:-0}"
fi
