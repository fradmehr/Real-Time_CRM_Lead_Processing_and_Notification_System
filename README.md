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
