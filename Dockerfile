FROM python:3.9

ADD ./app /app
WORKDIR /app
RUN pip3 install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"

CMD python3 manage.py runserver 0.0.0.0:$PORT
