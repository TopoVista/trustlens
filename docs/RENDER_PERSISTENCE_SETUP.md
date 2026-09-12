# TrustLens durable storage on Render

## Why this step matters

Render Free web-service files are ephemeral. SQLite works for local development, but documents stored on a free service's local disk can disappear after restart, redeploy, or idle spin-down. TrustLens uses durable Postgres automatically when the running backend has `DATABASE_URL`.

## Blueprint deployment

The repository's `render.yaml` declares a Postgres database named `trustlens-postgres` and maps its internal connection string to the web service's `DATABASE_URL`. For a Blueprint-managed service:

1. Open the Render Blueprint for this repository.
2. Sync or apply the Blueprint so Render creates or connects the database.
3. Verify the API service environment shows `DATABASE_URL` from the database binding.
4. Redeploy the API service.

## Existing manually created service

For a Render service created outside the Blueprint:

1. Create a Render Postgres database in the same region as the API.
2. Copy the database **internal** connection string.
3. Add it to the API service as secret `DATABASE_URL`.
4. Redeploy the API.

Do not put this connection string in Git, `backend/.env.example`, a Vercel environment variable, or any `VITE_` variable.

## Verify the running service

Sign in to the deployed product or send an authenticated request to:

```text
GET https://YOUR-RENDER-SERVICE.onrender.com/api/me/storage
```

Look for:

```json
{
  "storage_backend": "postgres",
  "durable": true
}
```

`storage_backend: "sqlite"` and `durable: false` means the service did not receive a usable `DATABASE_URL`. The service can still run, but its source data is not durable on Render Free.

## What happens to earlier documents

Documents that were stored in an ephemeral SQLite deployment before Postgres was connected cannot be restored from the new database automatically. Re-ingest them once the storage endpoint confirms durable Postgres.

## Plan lifecycle

The availability and retention of a free Postgres database are controlled by Render's current plan terms. Check those terms before treating the free tier as a permanent backup or production-retention solution. For stronger operational guarantees, use an appropriate managed-database plan and backups.
