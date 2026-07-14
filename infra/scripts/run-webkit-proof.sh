#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PLAYWRIGHT_VERSION="$(
  node -p "require('./apps/web/node_modules/@playwright/test/package.json').version" 2>/dev/null \
    || node -p "require('./node_modules/@playwright/test/package.json').version" 2>/dev/null \
    || printf '1.61.1'
)"
IMAGE="${NUR_PLAYWRIGHT_IMAGE:-mcr.microsoft.com/playwright:v${PLAYWRIGHT_VERSION}-jammy}"
PROOF_DIR="${NUR_WEBKIT_PROOF_DIR:-$ROOT/proof/screenshots}"
LOG_DIR="$ROOT/proof/logs"
mkdir -p "$PROOF_DIR" "$LOG_DIR"

run_docker_webkit() {
  if ! docker info >/dev/null 2>&1; then
    return 1
  fi

  printf 'Running real WebKit mobile proof in official Playwright image: %s\n' "$IMAGE"
  timeout 240s docker run --rm \
    --network host \
    --ipc=host \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -e CI=1 \
    -e VITE_NUR_ENABLE_OMEGA_RESEARCH=true \
    -e NUR_ENABLE_OMEGA_RESEARCH=true \
    -e NUR_PROOF_DIR=/work/proof/screenshots \
    -v "$ROOT:/work" \
    -w /work \
    "$IMAGE" \
    bash -lc 'npm --workspace apps/web run e2e -- e2e/track-a-mobile-webkit.spec.ts e2e/v197-adjuncts.spec.ts --project=webkit-mobile' \
    2>&1 | tee "$LOG_DIR/webkit-mobile-proof.log"
}

run_local_webkit() {
  printf 'Running real local Playwright WebKit mobile proof.\n'
  CI=1 \
    VITE_NUR_ENABLE_OMEGA_RESEARCH=true \
    NUR_ENABLE_OMEGA_RESEARCH=true \
    NUR_PROOF_DIR="$PROOF_DIR" \
    npm --workspace apps/web run e2e -- e2e/track-a-mobile-webkit.spec.ts e2e/v197-adjuncts.spec.ts --project=webkit-mobile \
    2>&1 | tee "$LOG_DIR/webkit-mobile-proof.log"
}

if [[ "${NUR_FORCE_LOCAL_WEBKIT:-0}" == "1" ]]; then
  run_local_webkit
elif ! run_docker_webkit; then
  printf 'Docker WebKit container unavailable; falling back to local Playwright WebKit.\n'
  run_local_webkit
fi

for name in \
  webkit-mobile-hydrated-systems.png \
  webkit-mobile-real-map-lens.png \
  webkit-mobile-settings-v197-native.png \
  webkit-mobile-omega-dashboard.png \
  webkit-mobile-omega-why-changed.png \
  webkit-mobile-capsule-active-answer.png
do
  candidate="$PROOF_DIR/$name"
  if [[ "$name" == webkit-mobile-hydrated-systems.png || "$name" == webkit-mobile-real-map-lens.png ]]; then
    candidate="$ROOT/proof/track-a/$name"
  elif [[ "$name" == webkit-mobile-* ]]; then
    candidate="$ROOT/proof/sol-v197-adjuncts/$name"
  fi
  if [[ ! -s "$candidate" ]]; then
    printf 'Missing required WebKit screenshot: %s\n' "$candidate" >&2
    exit 1
  fi
done

printf 'WebKit mobile proof passed. Screenshots: %s\n' "$PROOF_DIR"
