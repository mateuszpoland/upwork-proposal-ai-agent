import os
import boto3
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter()

SAGEMAKER_ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT_NAME")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
BASIC_AUTH_USER = os.getenv("BASIC_AUTH_ADMIN_USER")
BASIC_AUTH_PASS = os.getenv("BASIC_AUTH_ADMIN_PASS")

client = boto3.client("sagemaker", region_name=AWS_REGION)

def get_current_user(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    correct_user = credentials.username == BASIC_AUTH_USER
    correct_pass = credentials.password == BASIC_AUTH_PASS
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return credentials.username

@router.post("/control/start-endpoint")
def start_endpoint(_: str = Depends(get_current_user)):
    try:
        client.start_endpoint(EndpointName=SAGEMAKER_ENDPOINT_NAME)
        return {"status": "starting", "endpoint": SAGEMAKER_ENDPOINT_NAME}
    except client.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Start failed: {str(e)}")

@router.post("/control/stop-endpoint")
def stop_endpoint(_: str = Depends(get_current_user)):
    try:
        client.stop_endpoint(EndpointName=SAGEMAKER_ENDPOINT_NAME)
        return {"status": "stopping", "endpoint": SAGEMAKER_ENDPOINT_NAME}
    except client.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Stop failed: {str(e)}")

@router.get("/control/status")
def get_endpoint_status(_: str = Depends(get_current_user)):
    try:
        response = client.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT_NAME)
        return {
            "status": response.get("EndpointStatus"),
            "creation_time": str(response.get("CreationTime")),
            "last_modified_time": str(response.get("LastModifiedTime")),
            "production_variants": response.get("ProductionVariants"),
        }
    except client.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")