import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        short_code = (event.get("pathParameters") or {}).get("short_code")

        if short_code:
            # Get analytics for a specific short URL
            response = table.get_item(Key={"short_code": short_code})
            item = response.get("Item")

            if not item:
                return {
                    "statusCode": 404,
                    "headers": headers,
                    "body": json.dumps({"error": "Short URL not found"}),
                }

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(
                    {
                        "short_code": item["short_code"],
                        "long_url": item["long_url"],
                        "click_count": int(item.get("click_count", 0)),
                        "created_at": int(item.get("created_at", 0)),
                        "last_accessed": int(item.get("last_accessed", 0)),
                    }
                ),
            }

        else:
            # List all URLs with analytics
            response = table.scan(Limit=100)
            items = response.get("Items", [])

            urls = [
                {
                    "short_code": item["short_code"],
                    "long_url": item["long_url"],
                    "click_count": int(item.get("click_count", 0)),
                    "created_at": int(item.get("created_at", 0)),
                    "last_accessed": int(item.get("last_accessed", 0)),
                }
                for item in items
            ]

            urls.sort(key=lambda x: x["click_count"], reverse=True)

            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"urls": urls, "total": len(urls)}),
            }

    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Failed to fetch analytics"}),
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error"}),
        }
