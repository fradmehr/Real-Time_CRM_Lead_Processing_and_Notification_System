import json
import boto3
import datetime
import os

s3 = boto3.client('s3')

RAW_BUCKET = os.environ.get("RAW_BUCKET")
DELAY_BUCKET = os.environ.get("DELAY_BUCKET")

def _extract_lead_id(payload):
    ev = payload.get("event", {}) if isinstance(payload, dict) else {}
    lead_id = ev.get("lead_id") or (ev.get("data") or {}).get("id")
    if not lead_id:
        lead_id = payload.get("lead_id")
    return lead_id

def lambda_handler(event, context):
    # Accept API Gateway proxy v1 or raw test event
    body = event.get("body") if isinstance(event, dict) else event
    if isinstance(body, str):
        try:
            data = json.loads(body)
        except Exception:
            data = {}
    elif isinstance(body, dict):
        data = body
    else:
        data = {}

    lead_id = _extract_lead_id(data)
    if not lead_id:
        raise Exception("lead_id not found in payload")

    raw_key = f"raw-event-files/crm_event_{lead_id}.json"
    s3.put_object(Bucket=RAW_BUCKET, Key=raw_key, Body=json.dumps(data))

    ready_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat() + "Z"
    delay_key = f"pending/{lead_id}.json"
    delay_payload = {
        "lead_id": lead_id,
        "raw_path": raw_key,
        "ready_at": ready_at,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    s3.put_object(Bucket=DELAY_BUCKET, Key=delay_key, Body=json.dumps(delay_payload))

    # If invoked via API Gateway, return 200
    return {
        "statusCode": 200,
        "body": json.dumps({"message":"accepted","lead_id":lead_id})
    }
