# File Completion Order

Fill the scaffold in this order so imports and dependencies remain understandable:

1. `requirements.txt`
2. `.env.example`
3. `app/config.py`
4. `app/db.py`
5. `app/constants.py`
6. `app/models.py`
7. `alembic.ini`
8. `alembic/env.py`
9. `alembic/script.py.mako`
10. `alembic/versions/0001_initial_schema.py`
11. `app/seed.py`
12. `app/exceptions.py`
13. `app/pricing.py`
14. `app/schemas.py`
15. `app/services/metering.py`
16. `app/services/reporting.py`
17. `app/routers/actions.py`
18. `app/routers/usage.py`
19. `app/services/stripe_service.py`
20. `app/routers/checkout.py`
21. `app/routers/webhooks.py`
22. `app/main.py`
23. `tests/conftest.py`
24. Remaining test files
25. `scripts/demo.py`
26. `Dockerfile`
27. `docker-compose.yml`
28. `.gitignore`
29. `.dockerignore`
30. `README.md`

After entering the code, run:

```bash
docker compose up --build
docker compose exec app pytest -q
```
