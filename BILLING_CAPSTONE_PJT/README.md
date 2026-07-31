# Usage Billing and Quota API

A FastAPI capstone demonstrating idempotent usage metering, monthly quota enforcement, exact cost calculation, and Stripe test-mode subscription synchronization.

## Features

- Free and Pro plans
- Tenant-isolated data
- PostgreSQL persistence
- SQLAlchemy models
- Alembic migrations
- Docker Compose
- Idempotent billable actions
- Atomic quota enforcement
- 402 and 429 responses
- Exact integer-based cost calculations
- Cached-input token pricing
- Correct reasoning-token handling
- Stripe Checkout subscriptions
- Signature-verified Stripe webhooks
- Idempotent webhook processing
- Monthly usage reports
- Automated tests

## Architecture

```text
Client
  │
  │ X-Tenant-ID + Idempotency-Key
  ▼
FastAPI route
  ▼
MeteringService
  ├── lock tenant
  ├── deduplicate request
  ├── verify billing status
  ├── calculate current usage
  ├── enforce quota
  └── insert event
          ▼
      PostgreSQL

Stripe Checkout
  ▼
Signed webhook
  ▼
/webhooks/stripe
  ├── raw-body signature verification
  ├── event-ID deduplication
  └── tenant plan/status synchronization