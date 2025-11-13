import boto3

sqs = boto3.client('sqs')

sqs_url = "https://sqs.us-east-1.amazonaws.com/490225881732/ANB_SQS"

def add_video_to_process(video_id: int):
    message_body = str(video_id)
    response = sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=message_body
    )