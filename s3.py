import boto3

# Create an S3 client - Boto3 automatically uses the IAM role credentials
s3 = boto3.client('s3')

bucket_name = 'anb-s3-bucket'

def upload_file_to_bucket(file: str, s3_key: str):
    s3.upload_file(file, bucket_name, s3_key)


