FROM python:3.9.18
ENV PYTHONUNBUFFERED 1
RUN apt-get update -y
RUN apt-get install -y gettext inotify-tools curl
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
