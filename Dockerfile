FROM python:3

# Grab requirements and install them
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

# Grab the rest of the app
COPY ./app.py /app/app.py
COPY ./website /app/website
CMD python3 app.py


