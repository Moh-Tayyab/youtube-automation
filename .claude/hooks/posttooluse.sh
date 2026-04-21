#!/usr/bin/env bash
# =============================================================================
# bootlogix-hooks/posttooluse.sh — Quality gate: run AFTER every tool
# =============================================================================
# Validates outputs, checks video quality gates, enforces YouTube upload health.
# Fires after EVERY tool execution completes.
#
# Claude Code hook: reads stdin JSON with exit_code + tool_name + tool_args
# =============================================================================

set -euo pipefail

# Source shared library
HOOK_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
# shellcheck source=/home/muhammad_tayyab/bootlogix/.claude/hooks/lib.sh
source "$HOOK_SCRIPT_DIR/lib.sh"

# ---------------------------------------------------------------------------
# Parse stdin JSON from Claude Code
# ---------------------------------------------------------------------------
parse_input() {
  local input
  input=$(cat)
  EXIT_CODE=$(echo "$input" | jq -r '.exit_code // 0')
  TOOL_NAME=$(echo "$input" | jq -r '.tool_name // empty')
  TOOL_ARGS=$(echo "$input" | jq -r '.tool_args // empty')
}

# ---------------------------------------------------------------------------
# Main quality gate logic
# ---------------------------------------------------------------------------
main() {
  log_debug "posttooluse: tool='$TOOL_NAME' exit_code='$EXIT_CODE'"

  # -----------------------------------------------------------------------
  # Gate 1: Quality gate for video generation outputs
  # -----------------------------------------------------------------------
  if [[ "$EXIT_CODE" -eq 0 ]] && [[ "$TOOL_NAME" == "Bash" ]]; then
    # Only scan recently-created videos (modified in last 5 minutes)
    local now
    now=$(date +%s)

    for glob_pat in /tmp/bootlogix/output/*.mp4 "$BOOTLOGIX_PROJECT_DIR/output/"*.mp4 /tmp/*.mp4; do
      shopt -s nullglob
      for video_file in $glob_pat; do
        local mtime
        mtime=$(stat -c %Y "$video_file" 2>/dev/null || stat -f %m "$video_file" 2>/dev/null || true)
        if [[ -n "$mtime" ]] && (( now - mtime < 300 )); then
          log_info "Quality gating: $video_file"
          if command -v ffprobe &>/dev/null; then
            local size
            size=$(stat -c %s "$video_file" 2>/dev/null || stat -f %z "$video_file" 2>/dev/null || echo 0)
            if [[ "$size" -lt 1024 ]]; then
              log_error "QUALITY GATE FAILED: $video_file is only $size bytes"
            else
              log_info "Quality gate OK: $video_file (${size} bytes)"
            fi
          fi
        fi
      done
      shopt -u nullglob
    done
  fi

  # -----------------------------------------------------------------------
  # Gate 2: YouTube API health check after upload operations
  # -----------------------------------------------------------------------
  if [[ "$TOOL_NAME" == "Bash" ]] && echo "$TOOL_ARGS" | grep -qE "(youtube.*upload|upload.*youtube|yt-uploader)"; then
    if [[ "$EXIT_CODE" -eq 0 ]]; then
      log_info "Upload detected — running post-upload YouTube API health check"
      if ! bootlogix_healthcheck_youtube; then
        log_error "Post-upload YouTube API health check FAILED"
      fi
    fi
  fi

  # -----------------------------------------------------------------------
  # Gate 3: Flag failed tools
  # -----------------------------------------------------------------------
  if [[ "$EXIT_CODE" -ne 0 ]]; then
    log_warn "Tool '$TOOL_NAME' exited with code $EXIT_CODE"
  fi

  exit 0
}

# Entry point
parse_input
main
