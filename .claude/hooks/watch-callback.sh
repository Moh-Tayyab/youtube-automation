#!/usr/bin/env bash
# =============================================================================
# bootlogix-hooks/watch-callback.sh — Called when watch-folder detects a drop
# =============================================================================
# This is the callback that fires when inotifywait detects a new video file.
# It queues the file for SSD pipeline processing.
#
# Arguments: $1 = file path, $2 = event type (e.g., CLOSE_WRITE, MOVED_TO)
# =============================================================================

set -euo pipefail

HOOK_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$HOOK_SCRIPT_DIR/lib.sh"

bootlogix_watch_callback() {
  local file="$1"
  local event="$2"

  log_info "Watch callback: file='$file' event='$event'"

  # ---------------------------------------------------------------------------
  # Queue file for SSD pipeline
  # ---------------------------------------------------------------------------
  local queue_file="$BOOTLOGIX_TEMP_DIR/ssd-queue.md"
  mkdir -p "$(dirname "$queue_file")"

  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  cat >> "$queue_file" << EOF
- file: $file
  queued_at: $timestamp
  event: $event
EOF

  log_info "File queued for SSD pipeline: $file"

  # ---------------------------------------------------------------------------
  # Optional: send desktop notification (if notify-send is available)
  # ---------------------------------------------------------------------------
  if command -v notify-send &>/dev/null; then
    notify-send "bootlogix" "New video queued: $(basename "$file")" --icon=video-x-generic &
  fi
}

bootlogix_watch_callback "$@"
