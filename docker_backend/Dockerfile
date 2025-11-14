FROM python
WORKDIR /
COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt
COPY . .
EXPOSE 8000