import json
import boto3
import urllib.request
import os

s3 = boto3.client('s3')
ses = boto3.client('ses', region_name=os.environ.get("SES_REGION","us-east-1"))

RAW_BUCKET = os.environ.get("RAW_BUCKET")
DELAY_BUCKET = os.environ.get("DELAY_BUCKET")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET")
OWNER_LOOKUP_BUCKET = os.environ.get("OWNER_LOOKUP_BUCKET")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")

def send_email(lead_id, owner_data, raw_event):
    subj = f"New Lead Enriched: {owner_data.get('display_name') or lead_id}"
    body = f"""A new lead has been enriched.

Lead ID: {lead_id}
Name: {owner_data.get('display_name') or raw_event.get('event',{}).get('data',{}).get('display_name')}
Created Date: {owner_data.get('date_created') or raw_event.get('event',{}).get('data',{}).get('date_created')}
Label: {owner_data.get('status_label') or raw_event.get('event',{}).get('data',{}).get('status_label')}

Owner: {owner_data.get('lead_owner')}
Email: {owner_data.get('lead_email')}
Funnel: {owner_data.get('funnel')}

This message was generated automatically by the CRM Lead Pipeline.
"""
    ses.send_email(
        Source=EMAIL_FROM,
        Destination={'ToAddresses':[EMAIL_TO]},
        Message={
            'Subject':{'Data':subj},
            'Body':{'Text':{'Data':body}}
        }
    )

def lambda_handler(event, context):
    for rec in event.get("Records", []):
        bucket = rec.get("s3", {}).get("bucket", {}).get("name")
        key = rec.get("s3", {}).get("object", {}).get("key")
        if not bucket or not key:
            continue
        if not key.startswith("ready/"):
            continue

        try:
            resp = s3.get_object(Bucket=bucket, Key=key)
            ready_payload = json.loads(resp['Body'].read().decode())
        except Exception as e:
            print("error reading ready payload", e)
            continue

        lead_id = ready_payload.get("lead_id")
        raw_path = ready_payload.get("raw_path")

        try:
            rawobj = s3.get_object(Bucket=RAW_BUCKET, Key=raw_path)
            raw_event = json.loads(rawobj['Body'].read().decode())
        except Exception as e:
            print("error reading raw event", e)
            raw_event = {}

        lookup_url = f"https://{OWNER_LOOKUP_BUCKET}.s3.amazonaws.com/{lead_id}.json"
        owner_data = {}
        try:
            with urllib.request.urlopen(lookup_url, timeout=5) as resp:
                owner_data = json.loads(resp.read().decode())
        except Exception as e:
            print("owner lookup missing or failed:", e)
            owner_data = {
                "lead_owner": None,
                "lead_email": None,
                "funnel": None,
                "status_label": raw_event.get('event',{}).get('data',{}).get('status_label')
            }

        enriched = {
            "lead_id": lead_id,
            "raw_event": raw_event,
            "lookup_data": owner_data,
            "enriched_at": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }

        out_key = f"enriched/enriched_lead_{lead_id}.json"
        try:
            s3.put_object(Bucket=OUTPUT_BUCKET, Key=out_key, Body=json.dumps(enriched))
            print("wrote enriched", out_key)
        except Exception as e:
            print("error writing enriched", e)

        try:
            send_email(lead_id, owner_data, raw_event)
            print("sent email for", lead_id)
        except Exception as e:
            print("error sending email", e)

        try:
            s3.delete_object(Bucket=bucket, Key=key)
        except Exception as e:
            print("error deleting ready marker", e)
