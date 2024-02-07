FROM python:3.10.13-alpine
ENV PYTHONUNBUFFERED 1
ENV PYCURL_SSL_LIBRARY=openssl
RUN apk add --no-cache libcurl
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN apk add --no-cache --virtual .build-dependencies build-base curl-dev \
    && pip install -r requirements.txt \
    && apk del .build-dependencies
COPY . /app/
#RUN python /opt/manage.py check
