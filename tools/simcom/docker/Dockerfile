FROM ubuntu:20.04

ARG APP_DIR=/opt/simcom

# create directory for the app
RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR

# install python and pip
RUN apt-get update && apt-get install -y python3 python3-pip python-is-python3

# copy requirements file into container and install required python-libraries
COPY docker/requirements.txt $APP_DIR
RUN pip install -r $APP_DIR/requirements.txt

ENTRYPOINT ["tail", "-f", "/dev/null"]
