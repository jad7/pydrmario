# syntax=docker/dockerfile:1

FROM --platform=linux/amd64 python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt .
COPY server2.py .
RUN pip3 install -r requirements.txt
CMD [ "python3", "server2.py"]