FROM python:3

ADD ./app /app
WORKDIR /app
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/app"
