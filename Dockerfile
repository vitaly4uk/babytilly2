FROM python:3.9.5-slim
ENV PYTHONUNBUFFERED 1
ENV ENV LOCAL
#RUN apt-get update && apt-get install -y gettext inotify-tools python3-dev build-essential && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
