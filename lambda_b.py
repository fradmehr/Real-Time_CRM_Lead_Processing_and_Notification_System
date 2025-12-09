import json
import boto3
import datetime
import os

s3 = boto3.client('s3')

DELAY_BUCKET = os.environ.get("DELAY_BUCKET")
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS","60"))

def _parse_iso(ts):
    if ts.endswith("Z"):
        ts = ts.replace("Z","+00:00")
    return datetime.datetime.fromisoformat(ts)

def lambda_handler(event, context):
    for rec in event.get("Records", []):
        bucket = rec.get("s3", {}).get("bucket", {}).get("name")
        key = rec.get("s3", {}).get("object", {}).get("key")
        if not bucket or not key:
            continue
        if not key.startswith("pending/"):
            continue

        try:
            resp = s3.get_object(Bucket=bucket, Key=key)
            pending = json.loads(resp['Body'].read().decode())
        except Exception as e:
            print("Error reading pending:", e)
            continue

        lead_id = pending.get("lead_id")
        ready_at_raw = pending.get("ready_at")
        attempts = int(pending.get("attempts",0))

        try:
            ready_at = _parse_iso(ready_at_raw)
        except Exception:
            ready_at = datetime.datetime.utcnow()

        now = datetime.datetime.utcnow()

        if attempts >= MAX_ATTEMPTS:
            print(f"Max attempts reached for {lead_id}, moving to ready.")
            s3.put_object(Bucket=bucket, Key=f"ready/{lead_id}.json", Body=json.dumps(pending))
            s3.delete_object(Bucket=bucket, Key=key)
            continue

        if now >= ready_at:
            print(f"Ready time reached for {lead_id}. moving to ready/")
            s3.put_object(Bucket=bucket, Key=f"ready/{lead_id}.json", Body=json.dumps(pending))
            s3.delete_object(Bucket=bucket, Key=key)
        else:
            pending['attempts'] = attempts + 1
            pending['last_attempt'] = datetime.datetime.utcnow().isoformat() + "Z"
            try:
                s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(pending))
                print(f"Re-wrote pending for {lead_id} attempts={pending['attempts']}")
            except Exception as e:
                print("Error re-writing pending:", e)
