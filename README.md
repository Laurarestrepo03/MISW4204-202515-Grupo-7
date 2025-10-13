start app `uvicorn main:app --reload`
start celery `celery -A tasks worker -l info -P solo`