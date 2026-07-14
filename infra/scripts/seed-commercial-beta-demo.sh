#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/proof/100/commercial-beta-demo-script.md}"
mkdir -p "$(dirname "$OUT")"

cat > "$OUT" <<'EOF'
# NUR Commercial Beta Demo Script

## Roles
- Owner: creates a private Orbit, Talk turn, Plan step, and Context Capsule.
- Recipient: opens only the approved Capsule room and asks one scoped question.

## Demo Flow
1. Owner lands on Systems and confirms owner-ledger metrics are real counts.
2. Owner opens Talk, sends one line, sees provider status and structured response labels.
3. Owner uses "Use this move in Plan" to convert the next move into a Plan.
4. Owner opens Systems, creates a Capsule from an approved decision only.
5. Recipient opens the Capsule room and sees included/excluded boundaries.
6. Recipient asks a scoped question and receives a sourced answer.
7. Owner revokes the Capsule; recipient refresh shows revoked state with no cached answer.

## Proof Boundaries
- No fake AI output is used in production demo mode.
- No external research is fetched unless a future owner-enabled provider says so.
- No private source leaves a Capsule unless it appears in included sources.
- Native shell is not marketed as app-store ready; PWA is the current beta surface.
EOF

printf "%s\n" "$OUT"
