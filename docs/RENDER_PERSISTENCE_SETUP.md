# TrustLens durable storage on Render

Render Free web-service files are ephemeral: local SQLite data is deleted on a
restart, redeploy, or idle spin-down. TrustLens now uses a durable Postgres
database whenever `DATABASE_URL` is configured.

## One-time setup

The repository's `render.yaml` declares a `trustlens-postgres` database and
wires its internal connection string to `DATABASE_URL`. If the current service
is managed as a Render Blueprint, sync the Blueprint in the Render Dashboard
to create the database and apply that variable.

If the existing service was created manually instead of from the Blueprint:

1. In Render, create a **Postgres** database in the same region as the API.
2. Copy its **internal** connection string.
3. Add it to the API service as the secret environment variable
   `DATABASE_URL`.
4. Redeploy the API.

Do not commit the connection string to Git or place it in a frontend `VITE_`
variable. The API's storage panel shows **Durable DB** once it is connected.

## Important Free-plan limit

Render's Free Postgres option persists documents across API restarts, but
expires after 30 days. Upgrade the database before that deadline for lasting
production retention and backups. A paid web service plus a persistent disk is
an alternative, but managed Postgres is the safer fit for TrustLens's
relational workspace data.

Documents that disappeared before Postgres was connected were stored only on
the old ephemeral filesystem and cannot be recovered from Render. Re-ingest
them after the durable database is active.
