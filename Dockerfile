FROM python:3.9.7
ENV PYTHONUNBUFFERED 1
ENV ENV LOCAL
# RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev jpeg-dev zlib-dev libjpeg
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
