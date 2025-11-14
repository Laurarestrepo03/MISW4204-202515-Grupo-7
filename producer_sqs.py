import boto3
import json
import os
from botocore.exceptions import ClientError

sqs = boto3.client('sqs', region_name='us-east-1')

sqs_url = os.getenv('SQS_URL', '')

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