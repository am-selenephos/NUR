FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/api

# 1. Deterministic third-party layer: exact pinned tree from requirements.lock
#    (regenerate with infra/scripts/relock.sh when pyproject deps change).
RUN pip install --no-cache-dir pip==24.3.1
COPY apps/api/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock

# 2. Application source is copied BEFORE installing the package itself, so the
#    installed distribution actually contains `app` (previous ordering bug).
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
COPY apps/api/app ./app
RUN pip install --no-cache-dir --no-deps .

RUN useradd -m nur && chown -R nur /srv/api
USER nur
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
