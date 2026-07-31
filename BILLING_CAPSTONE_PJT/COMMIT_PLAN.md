# Recommended Commit Plan

You may create the complete folder hierarchy first. Git commits depend on what
you stage with `git add`, not on when the files were created.

## Commit 1 — Project scaffold and configuration

Add:

- `.gitignore`
- `.dockerignore`
- `.env.example`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `app/__init__.py`
- `app/config.py`
- `app/db.py`

Commands:

```bash
git add BILLING_CAPSTONE/.gitignore         BILLING_CAPSTONE/.dockerignore         BILLING_CAPSTONE/.env.example         BILLING_CAPSTONE/requirements.txt         BILLING_CAPSTONE/Dockerfile         BILLING_CAPSTONE/docker-compose.yml         BILLING_CAPSTONE/app/__init__.py         BILLING_CAPSTONE/app/config.py         BILLING_CAPSTONE/app/db.py

git commit -m "Set up billing capstone project and database configuration"
```

## Commit 2 — Data model and migrations

Add:

- `app/constants.py`
- `app/models.py`
- `app/seed.py`
- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/0001_initial_schema.py`

```bash
git add BILLING_CAPSTONE/app/constants.py         BILLING_CAPSTONE/app/models.py         BILLING_CAPSTONE/app/seed.py         BILLING_CAPSTONE/alembic.ini         BILLING_CAPSTONE/alembic

git commit -m "Add tenant billing data model and migrations"
```

## Commit 3 — Pricing, metering, and quota enforcement

Add:

- `app/exceptions.py`
- `app/pricing.py`
- `app/schemas.py`
- `app/services/__init__.py`
- `app/services/metering.py`
- `app/services/reporting.py`

```bash
git add BILLING_CAPSTONE/app/exceptions.py         BILLING_CAPSTONE/app/pricing.py         BILLING_CAPSTONE/app/schemas.py         BILLING_CAPSTONE/app/services

git commit -m "Implement idempotent metering quotas and cost calculation"
```

## Commit 4 — FastAPI endpoints

Add:

- `app/routers/__init__.py`
- `app/routers/actions.py`
- `app/routers/usage.py`
- `app/main.py`

```bash
git add BILLING_CAPSTONE/app/routers/__init__.py         BILLING_CAPSTONE/app/routers/actions.py         BILLING_CAPSTONE/app/routers/usage.py         BILLING_CAPSTONE/app/main.py

git commit -m "Add billable action and usage reporting APIs"
```

## Commit 5 — Stripe integration

Add:

- `app/services/stripe_service.py`
- `app/routers/checkout.py`
- `app/routers/webhooks.py`

```bash
git add BILLING_CAPSTONE/app/services/stripe_service.py         BILLING_CAPSTONE/app/routers/checkout.py         BILLING_CAPSTONE/app/routers/webhooks.py

git commit -m "Integrate Stripe Checkout and secure webhooks"
```

## Commit 6 — Tests

Add:

- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_metering.py`
- `tests/test_pricing.py`
- `tests/test_billing_status.py`
- `tests/test_webhooks.py`

```bash
git add BILLING_CAPSTONE/tests
git commit -m "Add billing quota pricing and webhook tests"
```

## Commit 7 — Demo and documentation

Add:

- `scripts/demo.py`
- `README.md`

```bash
git add BILLING_CAPSTONE/scripts/demo.py         BILLING_CAPSTONE/README.md

git commit -m "Document and demonstrate the billing capstone"
```

## Important

Creating all files at once does not force you to commit all files at once.
Only staged files are included in the next commit.

Check staged files before each commit:

```bash
git status
git diff --staged
```
