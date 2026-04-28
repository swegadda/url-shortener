import json
import os
import time
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        short_code = (event.get("pathParameters") or {}).get("short_code")

        if not short_code:
            return {
                "statusCode": 400,
                "headers": {**headers, "Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing short code"}),
            }

        response = table.get_item(Key={"short_code": short_code})
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": {**headers, "Content-Type": "application/json"},
                "body": json.dumps({"error": "Short URL not found"}),
            }

        # Increment click count and record last accessed time
        table.update_item(
            Key={"short_code": short_code},
            UpdateExpression="SET click_count = click_count + :inc, last_accessed = :ts",
            ExpressionAttributeValues={":inc": 1, ":ts": int(time.time())},
        )

        return {
            "statusCode": 301,
            "headers": {**headers, "Location": item["long_url"]},
            "body": "",
        }

    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return {
            "statusCode": 500,
            "headers": {**headers, "Content-Type": "application/json"},
            "body": json.dumps({"error": "Failed to redirect"}),
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "headers": {**headers, "Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }
