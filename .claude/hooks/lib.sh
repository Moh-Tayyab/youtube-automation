#!/usr/bin/env bash
# =============================================================================
# bootlogix-hooks/lib.sh — Shared library for bootlogix Claude Code hooks
# =============================================================================
# Provides: logging, secrets detection, credential freshness checks,
# YouTube API health, watch-folder management, and session memory utilities.
#
# All hooks source this library first. Never execute lib.sh directly.
# =============================================================================

set -euo pipefail

BOOTLOGIX_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTLOGIX_PROJECT_DIR="$(cd "$BOOTLOGIX_HOOKS_DIR/../.." && pwd)"
BOOTLOGIX_MEMORY_DIR="$BOOTLOGIX_PROJECT_DIR/memory"
BOOTLOGIX_TEMP_DIR="/tmp/bootlogix"
BOOTLOGIX_VIDEO_MANIFEST="$BOOTLOGIX_TEMP_DIR/video_manifest.txt"

# ---------------------------------------------------------------------------
# Security Configuration
# ---------------------------------------------------------------------------
# Maps command patterns to their risk level:
# - 'block': Stop the operation immediately (exit 1)
# - 'warn': Allow the operation but log a high-visibility warning
# ---------------------------------------------------------------------------
BOOTLOGIX_SECURITY_GATES=(
  "block|git\s+push\s+.*--force|BLOCKED: git push --force would destroy remote history. Use --force-with-lease instead."
  "block|rm\s+(-[rf]+\s+)?/\s|BLOCKED: rm -rf / detected — catastrophic operation."
  "block|rm\s+(-[rf]+\s+)?/$|BLOCKED: rm -rf / detected — catastrophic operation."
  "block|git\s+reset\s+--hard|BLOCKED: git reset --hard destroys uncommitted changes. Use git stash instead."
  "block|git\s+clean\s+-[fd]+|BLOCKED: git clean removes untracked files permanently."
  "block|git\s+add.*\.env|BLOCKED: staging .env file risks committing secrets."
  "warn|git\s+checkout\s+-b\s+main|WARNING: Creating a branch named 'main' might conflict with the primary branch."
  "warn|curl\s+.*-X\s+DELETE|WARNING: Destructive API call (DELETE) detected."
)

# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------
# Verifies that all required binaries are installed.
# Returns 0 (ok), 1 (missing dependencies).
bootlogix_check_dependencies() {
  local deps=("jq" "inotifywait" "ffprobe" "curl")
  local missing=()

  for dep in "${deps[@]}"; do
    if ! command -v "$dep" &>/dev/null; then
      missing+=("$dep")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Missing required dependencies: ${missing[*]}"
    return 1
  fi

  return 0
}

# ---------------------------------------------------------------------------
# Log levels
# ---------------------------------------------------------------------------
LOG_INFO=1 LOG_WARN=2 LOG_ERROR=3 LOG_DEBUG=0
HOOK_LOG_LEVEL="${HOOK_LOG_LEVEL:-$LOG_INFO}"

bootlogix_log() {
  local level="$1"; shift
  local msg="$*"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local level_str
  case "$level" in
    $LOG_DEBUG) level_str="DEBUG" ;;
    $LOG_INFO)  level_str="INFO " ;;
    $LOG_WARN)  level_str="WARN " ;;
    $LOG_ERROR) level_str="ERROR" ;;
    *)          level_str="TRACE" ;;
  esac
  printf '[bootlogix-hooks] [%s] [%s] %s\n' "$timestamp" "$level_str" "$msg" >&2
}

log_info()  { bootlogix_log $LOG_INFO  "$@"; }
log_warn()  { bootlogix_log $LOG_WARN  "$@"; }
log_error() { bootlogix_log $LOG_ERROR "$@"; }
log_debug() { bootlogix_log $LOG_DEBUG "$@"; }

# ---------------------------------------------------------------------------
# Secrets detection — patterns that should NEVER be committed
# ---------------------------------------------------------------------------
# Returns 0 (pass) if no secrets detected, 1 (fail) if secrets found.
# Prints matching patterns to stderr.
bootlogix_detect_secrets() {
  local file="$1"
  local detected=0

  # Credential file patterns (absolute paths that are dangerous to commit)
  local dangerous_patterns=(
    "client_secrets"
    "credentials\.json"
    "service_account\.json"
    "token\.json"
    "\.env$"
    "secrets\.yaml"
    "secrets\.yml"
    "\.netrc"
    "aws_access_key"
    "aws_secret_key"
    "sk_live_"
    "sk_test_"
    "ghp_"
    "AIza"
    "ya29\."
    "youtube\.api\.key"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
  )

  for pattern in "${dangerous_patterns[@]}"; do
    if grep -IqE "$pattern" "$file" 2>/dev/null; then
      log_error "SECRETS DETECTED in '$file': pattern '$pattern'"
      grep -InE "$pattern" "$file" 2>/dev/null | head -5 >&2
      detected=1
    fi
  done

  return $detected
}

# ---------------------------------------------------------------------------
# Credential freshness check
# ---------------------------------------------------------------------------
# Checks if OAuth tokens are expired or expiring within $1 seconds.
# Returns 0 (fresh) if tokens are valid, 1 (stale) if expired/expiring soon.
# Usage: bootlogix_check_token_freshness 86400  (warn if expiring within 24h)
bootlogix_check_token_freshness() {
  local warn_threshold="${1:-86400}"  # default: warn if < 24h left
  local token_dirs=(
    "$HOME/.credentials"
    "$HOME/.config/youtube-credentials"
    "$BOOTLOGIX_PROJECT_DIR/.credentials"
  )

  for dir in "${token_dirs[@]}"; do
    local token_file="$dir/client_secrets.json"
    if [[ -f "$token_file" ]]; then
      # Check for expiry field in token file (Google-style)
      local expiry
      expiry=$(grep -o '"expiry"[[:space:]]*:[[:space:]]*"[^"]*"' "$token_file" 2>/dev/null | head -1 | sed 's/.*"expiry"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
      if [[ -n "$expiry" ]]; then
        local expiry_epoch expiry_left
        # Try GNU date first (Linux), fall back to BSD date (macOS)
        expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null) \
          || expiry_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$expiry" +%s 2>/dev/null) \
          || expiry_epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$expiry" +%s 2>/dev/null) \
          || continue
        expiry_left=$((expiry_epoch - $(date +%s)))
        if [[ $expiry_left -lt 0 ]]; then
          log_error "Token EXPIRED: $token_file (expired at $expiry)"
          return 1
        elif [[ $expiry_left -lt $warn_threshold ]]; then
          log_warn "Token expiring soon: $token_file (${expiry_left}s left)"
          return 1
        fi
      fi
    fi
  done

  return 0
}

# ---------------------------------------------------------------------------
# YouTube API health check
# ---------------------------------------------------------------------------
# Returns 0 (healthy) if YouTube API is reachable, 1 (unhealthy) otherwise.
# Usage: bootlogix_healthcheck_youtube
bootlogix_healthcheck_youtube() {
  local api_key="${YOUTUBE_API_KEY:-${API_KEYS_YOUTUBE:-}}"

  if [[ -z "$api_key" ]]; then
    # Try to read from project credentials
    local cred_file="$BOOTLOGIX_PROJECT_DIR/.credentials/youtube-api-key"
    if [[ -f "$cred_file" ]]; then
      api_key=$(cat "$cred_file")
    fi
  fi

  if [[ -z "$api_key" ]]; then
    log_warn "No YouTube API key found — skipping health check"
    return 0  # soft fail: don't block, just warn
  fi

  local response
  response=$(curl -s --max-time 10 \
    "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true&key=$api_key" \
    2>/dev/null || true)

  if echo "$response" | grep -q '"error"'; then
    local error_msg
    error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | head -1 | sed 's/"message":"//;s/"$//')
    log_error "YouTube API health check FAILED: $error_msg"
    return 1
  fi

  log_info "YouTube API health check OK"
  return 0
}

# ---------------------------------------------------------------------------
# Watch-folder trigger
# ---------------------------------------------------------------------------
# Sets up an inotifywait watch on a directory, fires a callback on file drops.
# Requires: inotify-tools (inotifywait)
#
# Usage:
#   bootlogix_watch_folder "$WATCH_DIR" "$CALLBACK_SCRIPT"
#
# This is meant to be run as a background daemon. The hook framework starts
# it; bootlogix_watch_folder blocks and never returns.
bootlogix_watch_folder() {
  local watch_dir="$1"
  local callback_script="$2"

  if ! command -v inotifywait &>/dev/null; then
    log_warn "inotifywait not found — install inotify-tools to enable watch-folder"
    return 1
  fi

  if [[ ! -d "$watch_dir" ]]; then
    log_warn "Watch directory does not exist: $watch_dir"
    return 1
  fi

  log_info "Watching $watch_dir for new files..."

  # Wait for CLOSE_WRITE (file written and closed = ready to process)
  # Use process substitution so 'file' and 'event' remain local to the while loop
  # (piping to while read spawns a subshell where variables are global — process subst avoids this)
  while read -r file event; do
    # Only process video files
    case "$file" in
      *.mp4|*.mov|*.avi|*.mkv|*.webm|*.flv)
        log_info "New video detected: $file (event: $event)"
        bash "$callback_script" "$file" "$event" &
        ;;
    esac
  done < <(inotifywait -m -e CLOSE_WRITE -e MOVED_TO \
    --format '%w%f %e' "$watch_dir" 2>/dev/null)
}

# ---------------------------------------------------------------------------
# Video Production Utilities
# ---------------------------------------------------------------------------
# Records a generated video file to the manifest for precise quality gating.
bootlogix_record_video() {
  local file="$1"
  mkdir -p "$BOOTLOGIX_TEMP_DIR"
  echo "$(date +%s)|$file" >> "$BOOTLOGIX_VIDEO_MANIFEST"
}

# Retrieves the most recent video generated.
bootlogix_get_last_video() {
  if [[ -f "$BOOTLOGIX_VIDEO_MANIFEST" ]]; then
    tail -n 1 "$BOOTLOGIX_VIDEO_MANIFEST" | cut -d'|' -f2
  fi
}

# Cleans up the video manifest.
bootlogix_clear_video_manifest() {
  rm -f "$BOOTLOGIX_VIDEO_MANIFEST"
}

# ---------------------------------------------------------------------------
# Session memory — snapshot current session state for next session
# ---------------------------------------------------------------------------
# Writes session context to memory/ so the next session can warm up fast.
bootlogix_session_save() {
  local session_label="${1:-$(date '+%Y%m%d-%H%M%S')}"
  local memory_file="$BOOTLOGIX_MEMORY_DIR/session-snapshot.md"

  mkdir -p "$BOOTLOGIX_MEMORY_DIR"

  local active_tasks=""
  if command -v claude &>/dev/null; then
    active_tasks=$(claude --print "Current tasks: " 2>/dev/null | head -20 || true)
  fi

  local git_status
  git_status=$(git -C "$BOOTLOGIX_PROJECT_DIR" status --short 2>/dev/null | head -20 || true)

  local hook_meta="Saved: $(date '+%Y-%m-%d %H:%M:%S')"

  cat > "$memory_file" << EOF
---
name: last-session
description: "Last session snapshot for warm restarts"
type: project
---

# Session Snapshot — $session_label

$hook_meta

## Active Work
$active_tasks

## Git Status (last session)
\`\`\`
$git_status
\`\`\`

## Last Session Label
\`$session_label\`
EOF

  log_info "Session snapshot saved to $memory_file"
}

# ---------------------------------------------------------------------------
# Credential injection — populate env vars from secure storage
# ---------------------------------------------------------------------------
# Reads API keys from secure storage and exports them to session env.
# Supports: pass (password store), env files (restricted).
bootlogix_load_credentials() {
  # Try password store first (most secure)
  if command -v pass &>/dev/null; then
    if pass show bootlogix/youtube-api-key &>/dev/null; then
      export YOUTUBE_API_KEY=$(pass show bootlogix/youtube-api-key 2>/dev/null || true)
      log_debug "Loaded YouTube API key from pass"
    fi
    if pass show bootlogix/anthropic-api-key &>/dev/null; then
      export ANTHROPIC_API_KEY=$(pass show bootlogix/anthropic-api-key 2>/dev/null || true)
      log_debug "Loaded Anthropic API key from pass"
    fi
  fi

  # Fallback: project .credentials dir (gitignored)
  local cred_dir="$BOOTLOGIX_PROJECT_DIR/.credentials"
  if [[ -d "$cred_dir" ]]; then
    for cred_file in "$cred_dir"/*.key "$cred_dir"/*-api-key "$cred_dir"/.env; do
      [[ -f "$cred_file" ]] || continue
      local cred_name
      cred_name=$(basename "$cred_file" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
      # Don't override if already set (pass takes priority)
      export "${cred_name}"="$(cat "$cred_file")"
      log_debug "Loaded $cred_name from $cred_file"
    done
  fi
}
