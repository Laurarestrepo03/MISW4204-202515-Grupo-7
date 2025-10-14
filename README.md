start app `uvicorn main:app --reload` <br>
start celery `celery -A tasks worker -l info -P solo`