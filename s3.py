import boto3
import os

s3 = boto3.client('s3')

bucket_name = os.getenv('S3_BUCKET', 'anb-s3-bucket')

def upload_file_to_bucket(file_path: str, s3_path: str):
    s3.upload_file(file_path, bucket_name, s3_path)

def retrieve_file_from_bucket(video_name: str):
    # (bucket_name, s3_path, local_path)
    s3.download_file(bucket_name, "original_videos/"+video_name, "temp_files/original/"+video_name)
