#!/usr/bin/env bash
# Release-facing naming regression guard.
#
# The public product identity is NUR (Neural Upgrade Rewiring). The front-door
# release surface — the docs and scripts a user sees first and that ship in the
# distributable archive — must not carry build-process, donor, rescue-branch,
# competition, or builder-agent terminology. Internal construction/design
# history under docs/ is intentionally NOT scanned; it is a development record.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Explicit release surface. Add new public-facing docs/scripts here as they land.
RELEASE_SURFACE=(
  README.md
  QUICKSTART_BOOT.md
  RUNBOOK.md
  SECURITY_NOTES.md
  DEMO_SCRIPT.md
  package.json
  START_NUR.sh
  RUN_NUR.sh
)
# Boot/operations scripts are release-facing too (they ship and are user-run),
# except this scanner and the historical execution ledger.
while IFS= read -r script; do
  case "$script" in
    infra/scripts/release-naming-scan.sh) continue ;;
  esac
  RELEASE_SURFACE+=("$script")
done < <(find infra/scripts -maxdepth 1 -name '*.sh' | sort)

# Forbidden public tokens (case-insensitive, word/token boundaries where useful).
FORBIDDEN='build[ -]?week|lane[ -]?[ab]\b|rescue/lane|\bcodex\b|\bcousin\b|\bfable\b|\bopus\b|\bclaude\b|donor repo|am-selenephos|am-statementforge'

status=0
for path in "${RELEASE_SURFACE[@]}"; do
  [[ -f "$path" ]] || continue
  if hits="$(grep -niE "$FORBIDDEN" "$path" 2>/dev/null)"; then
    printf 'NAMING VIOLATION in %s:\n%s\n\n' "$path" "$hits"
    status=1
  fi
done

if [[ "$status" -ne 0 ]]; then
  printf 'release-naming-scan: FAIL — release-facing files carry non-public naming.\n' >&2
  exit 1
fi
printf 'release-naming-scan: PASS — release surface uses only public NUR naming.\n'
