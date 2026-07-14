# Security Notes

## Secrets

- `.env` and `.env.local` are excluded from the bootable package.
- OpenAI keys must be entered only with
  `infra/scripts/configure-openai-local.sh`.
- The frontend never reads `OPENAI_API_KEY`.
- `infra/scripts/secret-scan.sh` scans source, frontend dist, reports, traces,
  logs, proof, and evidence artifacts for OpenAI key and bearer-token patterns.

## AI Provider

Default boot mode is:

```text
NUR_AI_PROVIDER=disabled
```

Disabled mode is honest. It does not fake model output. OpenAI mode requires a
server-side `.env.local` and a configured model.

## RLS

The runtime role is `nur_app` with `NOBYPASSRLS`. Omega tables use forced
owner-only RLS, including:

- `omega_experiences`
- `omega_claims`
- `omega_evidence_edges`
- `omega_contradictions`
- `omega_workspace_frames`
- `omega_predictions`
- `omega_learning_proposals`
- `omega_consolidation_runs`
- `omega_review_queue`

Capsule recipient grants are separate from Omega owner memory and do not grant
access to Omega tables.

## Omega Limits

Omega v1 is a governed research layer. It does not claim sentience, AGI,
consciousness, soul, feelings, free will, or autonomous external action. It
does not expose chain-of-thought. Learning proposals require owner approval and
cannot rewrite RLS, auth, secrets, recipient grants, or autonomous action
policy.

## Packaging

`infra/scripts/package-bootable.sh` excludes:

- `.env`, `.env.local`, other `.env.*` files except `.env.example`
- `node_modules`
- build/dist output
- `.git`
- database dumps and runtime volumes
- logs, traces, proof, evidence, and screenshots
- secret directories
