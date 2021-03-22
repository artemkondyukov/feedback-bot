# set base image (host OS)
FROM python:3.8

WORKDIR /code

RUN mkdir /data

COPY requirements.txt .
COPY token .

RUN pip install -r requirements.txt

COPY src/ src/
COPY data/ data/

CMD [ "python", "src/main.py" ]