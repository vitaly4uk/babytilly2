FROM python:3.9.10
ENV PYTHONUNBUFFERED 1
ENV ENV LOCAL
RUN apt update && apt install -y locales
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:en
ENV LC_ALL ru_RU.UTF-8
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
