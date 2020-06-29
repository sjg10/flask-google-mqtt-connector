FROM python:3

# Grab requirements and install them
COPY ./requirements.txt /code/requirements.txt
WORKDIR /code
RUN pip3 install -r requirements.txt

# Grab the rest of the app
COPY ./app.py /code/app.py
COPY ./website /code/website
CMD python3 app.py


