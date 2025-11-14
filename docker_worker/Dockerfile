FROM python
WORKDIR /
COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt
COPY database.py models.py s3.py worker_sqs.py .env ./
COPY assets/anb_logo.mp4 .
CMD ["python3", "worker_sqs.py"]