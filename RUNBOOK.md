# Runbook

## Start

```bash
bash RUN_NUR.sh
```

This starts Postgres, Redis, the FastAPI server, Celery worker, Celery beat, and
Vite, runs health checks, seeds the local demo, and opens the browser. Runtime
PIDs and logs live under `.nur-runtime/`.

## Status

```bash
bash RUN_NUR.sh status
```

Expected local URLs:

- Web: `http://localhost:5173`
- API health: `http://localhost:8000/healthz`
- API ready: `http://localhost:8000/readyz`
- Metrics: `http://localhost:8000/metrics`

## Logs

```bash
bash RUN_NUR.sh logs
```

The logs helper redacts common key/token patterns before printing.

## Stop

```bash
bash RUN_NUR.sh stop
```

This stops local PIDs and compose services. The named Postgres volume remains
until removed manually.

## Reset Local Data

```bash
bash RUN_NUR.sh reset-demo
```

## Package

```bash
bash RUN_NUR.sh package
```

The packager excludes `.env`, `.env.local`, node modules, build outputs,
runtime logs, DB files, proof artifacts, and `.git`; then it runs the secret
scan and writes a SHA-256 sidecar.
