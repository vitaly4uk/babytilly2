FROM python:3.9.10
ENV PYTHONUNBUFFERED 1
ENV ENV LOCAL
RUN apt update && apt install -y locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN mkdir -p /app
WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . /app/
#RUN python /opt/manage.py check
