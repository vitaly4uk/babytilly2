FROM python:3.9.7-slim
ENV PYTHONUNBUFFERED 1
ENV ENV LOCAL
#RUN apt-get update && apt-get install -y libcurl4-openssl-dev libssl-dev python3-dev
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
