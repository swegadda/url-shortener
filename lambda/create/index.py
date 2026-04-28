import json
import os
import string
import random
import time
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

SHORT_CODE_LENGTH = 7
ALLOWED_CHARS = string.ascii_letters + string.digits


def generate_short_code():
    return "".join(random.choices(ALLOWED_CHARS, k=SHORT_CODE_LENGTH))


def handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        long_url = body.get("url")

        if not long_url:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing 'url' in request body"}),
            }

        if not long_url.startswith(("http://", "https://")):
            long_url = "https://" + long_url

        short_code = generate_short_code()
        timestamp = int(time.time())

        table.put_item(
            Item={
                "short_code": short_code,
                "long_url": long_url,
                "created_at": timestamp,
                "click_count": 0,
            },
            ConditionExpression="attribute_not_exists(short_code)",
        )

        base_url = os.environ.get("BASE_URL", "").rstrip("/")
        short_url = f"{base_url}/{short_code}" if base_url else short_code

        return {
            "statusCode": 201,
            "headers": headers,
            "body": json.dumps(
                {
                    "short_code": short_code,
                    "short_url": short_url,
                    "long_url": long_url,
                    "created_at": timestamp,
                }
            ),
        }

    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Failed to create short URL"}),
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error"}),
        }
