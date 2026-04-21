#!/usr/bin/env bash
# =============================================================================
# bootlogix-hooks/startup.sh — Run when Claude Code session STARTS
# =============================================================================
# Loads credentials, restores session memory, checks API health.
#
# Trigger: fires when Claude Code initializes a new session
# =============================================================================

set -euo pipefail

HOOK_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
# shellcheck source=/home/muhammad_tayyab/bootlogix/.claude/hooks/lib.sh
source "$HOOK_SCRIPT_DIR/lib.sh"

log_info "bootlogix hooks: startup sequence beginning"

# ---------------------------------------------------------------------------
# 0. Environment Health Check
# ---------------------------------------------------------------------------
if ! bootlogix_check_dependencies; then
  log_error "Critical dependencies missing. Some hooks may fail."
  # We don't exit 1 here because we don't want to block the entire Claude session,
  # but we warn the user loudly.
fi

# ---------------------------------------------------------------------------
# 1. Load credentials from secure storage
# ---------------------------------------------------------------------------
bootlogix_load_credentials

# ---------------------------------------------------------------------------
# 2. Session warm start — load last session snapshot
# ---------------------------------------------------------------------------
memory_file="$BOOTLOGIX_MEMORY_DIR/session-snapshot.md"
if [[ -f "$memory_file" ]]; then
  log_info "Found session snapshot from last session:"
  log_info "---"
  head -30 "$memory_file" >&2
  log_info "---"
else
  log_info "No previous session snapshot found — fresh start"
fi

# ---------------------------------------------------------------------------
# 3. Check credential freshness (warn if tokens expiring)
# ---------------------------------------------------------------------------
if ! bootlogix_check_token_freshness 86400; then
  log_warn "Credential freshness check WARNING: tokens need attention"
fi

# ---------------------------------------------------------------------------
# 4. YouTube API health check (non-blocking)
# ---------------------------------------------------------------------------
if command -v curl &>/dev/null; then
  bootlogix_healthcheck_youtube || log_warn "YouTube API health check had warnings"
fi

# ---------------------------------------------------------------------------
# 5. Watch-folder daemon
# ---------------------------------------------------------------------------
watch_pid_file="$BOOTLOGIX_TEMP_DIR/watch-folder.pid"
if [[ -f "$watch_pid_file" ]]; then
  old_pid=$(cat "$watch_pid_file" 2>/dev/null || true)
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    log_info "Watch-folder daemon already running (PID $old_pid)"
  else
    log_info "Stale watch-folder PID — restarting..."
    "$HOOK_SCRIPT_DIR/watch.sh" &
    echo $! > "$watch_pid_file"
  fi
else
  log_info "Starting watch-folder daemon..."
  "$HOOK_SCRIPT_DIR/watch.sh" &
  echo $! > "$watch_pid_file"
fi

log_info "bootlogix hooks: startup sequence complete"
