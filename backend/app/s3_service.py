import os
from pathlib import Path
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3_client = boto3.client("s3", region_name=AWS_REGION)

def upload_file_to_s3(filename: str, key: str) -> str:
    s3_client.upload_file(Filename=filename, Bucket=AWS_S3_BUCKET, Key=key, ExtraArgs={"ContentType": "Image/png"},)
    return key

def get_s3_object_byte(key: str) -> bytes:
    response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=key)
    return response["Body"].read()

def delete_s3_object(key: str):
    s3_client.delete_object(Bucket=AWS_S3_BUCKET, Key=key)