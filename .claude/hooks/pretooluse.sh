#!/usr/bin/env bash
# =============================================================================
# bootlogix-hooks/pretooluse.sh — Security gate: run BEFORE every tool
# =============================================================================
# Blocks dangerous operations and validates credential safety.
#
# Trigger: fires before ANY tool execution (bash, read, edit, write, etc.)
# Fail action: exits non-zero -> tool is blocked
# Pass action: exits zero -> tool proceeds
# =============================================================================

set -euo pipefail

# Source shared library
HOOK_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HOOK_SCRIPT_DIR/lib.sh"

# ---------------------------------------------------------------------------
# Parse stdin JSON from Claude Code
# ---------------------------------------------------------------------------
parse_input() {
  local input
  input=$(cat)
  TOOL_NAME=$(echo "$input" | jq -r '.tool_name // empty')
  TOOL_ARGS=$(echo "$input" | jq -r '.tool_args // empty')
}

# ---------------------------------------------------------------------------
# Main gate logic
# ---------------------------------------------------------------------------
main() {
  # Load credentials so we can check token freshness
  bootlogix_load_credentials

  log_debug "pretooluse: tool='$TOOL_NAME'"

  # -----------------------------------------------------------------------
  # Gate 1: Command Security Gates (using BOOTLOGIX_SECURITY_GATES)
  # -----------------------------------------------------------------------
  if [[ "$TOOL_NAME" == "Bash" ]]; then
    for gate in "${BOOTLOGIX_SECURITY_GATES[@]}"; do
      # Split the gate string into action, pattern, and message
      action=$(echo "$gate" | cut -d'|' -f1)
      pattern=$(echo "$gate" | cut -d'|' -f2)
      message=$(echo "$gate" | cut -d'|' -f3-)

      if echo "$TOOL_ARGS" | grep -qE "$pattern"; then
        if [[ "$action" == "block" ]]; then
          log_error "$message"
          exit 1
        elif [[ "$action" == "warn" ]]; then
          log_warn "$message"
        fi
      fi
    done
  fi

  # -----------------------------------------------------------------------
  # Gate 2: SECRETS SCAN on file write targets
  # -----------------------------------------------------------------------
  if [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Bash" ]]; then
    local potential_files
    # Extract paths from JSON tool_args if they exist, otherwise find paths in the string
    potential_files=$(echo "$TOOL_ARGS" | grep -oE '"file_path":\s*"[^"]*"' | sed 's/"file_path":\s*"//;s/"$//g' || true)
    potential_files+=$'\n'
    potential_files+=$(echo "$TOOL_ARGS" | grep -oE '(^|/)[a-zA-Z0-9._-]+(/[a-zA-Z0-9._-]+)*' | grep -vE '^(git|curl|wget|npm|node|python)' || true)

    # Use process substitution to avoid pipe subshell so exit 1 kills the parent
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      case "$file" in
        /tmp/*|/proc/*|/sys/*|/dev/*) continue ;;
      esac
      if [[ -f "$file" ]] && bootlogix_detect_secrets "$file"; then
        log_error "BLOCKED: file '$file' contains secrets"
        exit 1
      fi
    done < <(echo "$potential_files")
  fi

  # -----------------------------------------------------------------------
  # Gate 3: CREDENTIAL freshness check (warn if tokens expiring soon)
  # -----------------------------------------------------------------------
  if ! bootlogix_check_token_freshness 86400; then
    log_warn "Credential freshness check failed — tokens may need refresh"
  fi

  exit 0
}

# Entry point — parse input then run gates
parse_input
main
