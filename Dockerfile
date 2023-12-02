FROM python:3.11.1-alpine

LABEL maintainer="olehoryshshuk@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR social_media_API/

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /media
RUN mkdir -p /static

RUN adduser \
        --disabled-password \
        --no-create-home \
        social_media_user

RUN chown -R social_media_user:social_media_user /media/
RUN chown -R social_media_user:social_media_user /static/

RUN chmod -R 755 /media/
RUN chmod -R 755 /static/

USER social_media_user
