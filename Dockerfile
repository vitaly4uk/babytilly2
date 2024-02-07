FROM python:3.10.13-alpine
ENV PYTHONUNBUFFERED 1
ENV PYCURL_SSL_LIBRARY=openssl
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN apk add --no-cache --virtual .build-dependencies build-base curl-dev bash libcurl && pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
