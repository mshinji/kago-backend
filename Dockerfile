FROM python:3.9

ADD ./app /app
WORKDIR /app
RUN pip3 install -r requirements.txt
