# Runbook: backend on AWS (dev)

Stack `pmap-dev-backend` (`infra/backend.yaml`), region `eu-north-1`. It uses the stacks of extraction:
`pmap-dev-network` (VPC, security group, `pmap-dev.internal`), `pmap-dev-data` (Redis) and
`pmap-dev-extraction` (its API key). Deploy extraction first. Run everything from the repo root.

## 1. Deploy main by hand

```bash
aws login
git checkout main && git pull
make deploy
make aws-check
```

`deploy` = image of HEAD (tag = short commit, built once) → stack update with api and worker running.
The first deploy creates the stack with nothing running, pushes the image, then starts both services.

- Remove `AWS_...` lines from `.env` before deploying by hand: make exports `.env`, and expired keys there
  override `aws login`.
- No migrations: backend has no database. Redis database 1 keeps its queue apart from extraction's (0).
- Exports go to the stack's own bucket `pmap-dev-backend-exports-<account>`; download links are valid for an hour.
  For local tests after the first deploy: `S3_BUCKET` in `.env` = output `ExportBucketName` of the stack.

## 2. How backend is reached

- Backend → extraction: `http://extraction.pmap-dev.internal:8000` with the key of extraction. Extraction
  must be running, otherwise backend answers 502.
- Gateway → backend: `http://backend.pmap-dev.internal:8000`. Port 8000 is not open to the internet:
  the gateway will be the only public entry.
- Until then, from your machine only: set `AdminCidr` of the network stack (extraction repo) to your IP.

  ```bash
  aws cloudformation deploy --stack-name pmap-dev-network --template-file infra/network.yaml \
    --parameter-overrides AdminCidr="$(curl -s https://checkip.amazonaws.com)/32"   # in the extraction repo
  make aws-api-url      # http://<ip>:8000, changes after every deploy
  ```

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
