import json
import boto3

runtime = boto3.client("sagemaker-runtime")

def lambda_handler(event, context):
    try:
        input_data = event.get("body")
        endpoint_name = 'rag-worker-endpoint-prod'

        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=input_data
        )

        result = response["Body"].read().decode("utf-8")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": result
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }