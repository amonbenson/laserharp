FROM python:latest

# upgrade packet managers
RUN apt-get update && apt-get upgrade -y
RUN pip install --upgrade pip

# install additional system requirements
RUN apt-get install -y libasound2-dev alsa-utils ffmpeg libsm6 libxext6

# install dependencies
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install numpy opencv-python

# copy remaining files
COPY ./laserharp /app/laserharp

# configuration env variables

# run emulator
CMD python -m laserharp
