# Runbook: backend on AWS (dev)

Stacks `pmap-dev-backend` (`infra/backend.yaml`) and `pmap-dev-gateway` (`infra/gateway.yaml`), region
`eu-north-1`. They use the stacks of extraction: `pmap-dev-network` (VPC, security group,
`pmap-dev.internal`), `pmap-dev-data` (RDS, Redis) and `pmap-dev-extraction` (its API key). Deploy
extraction first. Run everything from the repo root.

## 1. Deploy main by hand

```bash
aws login
git checkout main && git pull
make deploy
make aws-check
```

`deploy` = image of HEAD (tag = short commit, built once) → stack update with nothing running →
`alembic upgrade head` as a one-off task → api and worker running.
The first deploy creates the stack with nothing running, pushes the image, then starts both services.

- Remove `AWS_...` lines from `.env` before deploying by hand: make exports `.env`, and expired keys there
  override `aws login`.
- Database `backend` on the RDS instance of extraction, same master user. Create it once before the first
  deploy, through the tunnel of extraction (`make tunnel-db` in the extraction repo):
  `psql "postgresql://pmap_admin@127.0.0.1:15432/extraction?sslmode=require" -c 'CREATE DATABASE backend'`.
- Users: `make aws-create-user LOGIN=admin` (asks for the password; `ROLE=user` for a plain user).
- Redis database 1 keeps its queue apart from extraction's (0).
- Exports go to the stack's own bucket `pmap-dev-backend-exports-<account>`; download links are valid for an hour.
  For local tests after the first deploy: `S3_BUCKET` in `.env` = output `ExportBucketName` of the stack.

## 2. How backend is reached

- Backend → extraction: `http://extraction.pmap-dev.internal:8000` with the key of extraction. Extraction
  must be running, otherwise backend answers 502.
- Clients → gateway: `make gateway` deploys `infra/gateway.yaml` and prints its URL. `/auth/*`, `/docs` and
  the reads (`GET /transactions`, `/territories`, `/analytics/*`, `/health`) need no token; everything
  else needs `Authorization: Bearer <access_token>`; `/internal/*` is closed.
- Gateway → backend: through a VPC link to `backend-api.pmap-dev.internal:8000`; the authorizer calls
  `/internal/users/{id}` there. The JWT secret `pmap/dev/jwt` is copied into the authorizer on deploy:
  after changing it, run `make deploy` and `make gateway`.
- Port 8000 is never open to the internet (`network.yaml` of extraction has no rule for it): use the gateway.

- New extraction key: the backend secret copies it on a stack update, so redeploy backend after it.

## 3. CI/CD

```
PR        -> checks: ruff, pytest
push main -> checks -> deploy (GitHub machine): make deploy
```

Same IAM user as extraction (`pmap-dev-github-deploy`). In this repo: GitHub → Settings → Secrets and
variables → Actions → **Secrets** → `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (the same values).

## 4. When something fails

```bash
make aws-check
make aws-logs SINCE=1h
aws cloudformation describe-stack-events --stack-name pmap-dev-backend \
  --query "StackEvents[?contains(ResourceStatus,'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
```

| Error | Cause |
| --- | --- |
| `No export named pmap-dev-...` | network or data stack of extraction is missing |
| `Secrets Manager can't find the specified secret` | extraction stack is not deployed: no `pmap/dev/extraction-api-key` |
| `CannotPullContainerError` | no image with this tag in ECR |
| every request 502 | extraction is stopped, or its key changed: redeploy backend |
| export `failed` with `AccessDenied` | `S3_BUCKET` is not the bucket of this stack |
