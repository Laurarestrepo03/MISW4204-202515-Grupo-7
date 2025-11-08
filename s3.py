import boto3
import os

s3 = boto3.client('s3')

bucket_name = os.getenv('S3_BUCKET', 'anb-s3-bucket')

def upload_file_to_bucket(file: str, s3_key: str):
    s3.upload_file(file, bucket_name, s3_key)


