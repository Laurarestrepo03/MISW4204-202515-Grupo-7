import boto3
import json
from botocore.exceptions import ClientError

sqs = boto3.client('sqs', region_name='us-east-1')

sqs_url = "https://sqs.us-east-1.amazonaws.com/490225881732/ANB_SQS"

def send_message(video_id: int):
    try:
        payload = {
            'video_id': str(video_id)
        }
        response = sqs.send_message(
            QueueUrl = sqs_url,
            MessageBody = json.dumps(payload),

        )
        return True
    except ClientError as e:
        print(f"✗ Error al enviar mensaje: {e}")
        return False


def check_unprocessed_messages():
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=1,  # Receive one message at a time
        WaitTimeSeconds=10,     # Ena Retrieve all message attributes
    )