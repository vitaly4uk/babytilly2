FROM python:3.10.14-alpine
ENV PYTHONUNBUFFERED 1
ENV PYCURL_SSL_LIBRARY=openssl
RUN apk add --no-cache --virtual .build-dependencies build-base curl-dev bash libcurl
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip && pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
