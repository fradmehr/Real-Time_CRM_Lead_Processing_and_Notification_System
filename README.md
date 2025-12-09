# CRM Lead Pipeline

This repository contains the code and CloudFormation to deploy the CRM Lead Pipeline using AWS Lambda + S3 + SES.

## Structure

- infra/cloudformation.yml — CloudFormation template to create buckets, roles, Lambdas, and S3 notifications.
- lambdas/ — source code for Lambda functions (A: webhook receiver, B: delay handler, C: enricher + SES).
- scripts/deploy.sh — deploy helper for CloudFormation.
- assets/architecture.png — architecture diagram.

## Deploy

1. Edit `infra/cloudformation.yml` if you want to change defaults.
2. Verify SES sender and recipient emails.
3. Run:

```bash
bash scripts/deploy.sh
```

## Testing

Invoke `lead_webhook_receiver` with a sample webhook payload (see README in repo for sample payload).

## Summary

# CRM Lead Pipeline


This repo contains source and infra for an automated lead ingestion and enrichment pipeline using AWS Lambda and S3. The system ingests Close CRM webhooks, waits 10 minutes for the CRM to assign an owner, looks up owner info from a public S3 bucket, enriches the lead data, stores the enriched file in S3, and notifies the team via SES email.


## Contents
- `infra/cloudformation.yml` — CloudFormation template to create S3 buckets, IAM roles, Lambdas, and S3 notifications.
- `lambdas/lambda_a.py` — Webhook receiver: writes raw event and pending marker.
- `lambdas/lambda_b.py` — Delay handler: S3-triggered loop until `ready_at`.
- `lambdas/lambda_c.py` — Enricher: merges data, writes enriched file, sends SES email.
- `scripts/deploy.sh` — helper script to deploy the CloudFormation stack.
