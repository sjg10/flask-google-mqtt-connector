FROM python:3.10-alpine

RUN apk add --update cargo rust py-cffi openssl-dev libffi-dev

RUN pip3 install -U pip

# Grab requirements and install them
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

# Grab the rest of the app
COPY ./app.py /app/app.py
COPY ./website /app/website
CMD python3 app.py


