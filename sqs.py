import boto3

sqs = boto3.client('sqs', region_name='us-east-1')

sqs_url = "https://sqs.us-east-1.amazonaws.com/490225881732/ANB_SQS"

def add_message(video_id: int):
    message_body = str(video_id)
    response = sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=message_body
    )

def check_unprocessed_messages():
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=1,  # Receive one message at a time
        WaitTimeSeconds=10,     # Ena Retrieve all message attributes
    )