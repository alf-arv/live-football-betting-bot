FROM ubuntu:latest

MAINTAINER Alf Arv

CMD tail -f /dev/null

RUN apt-get update -y && apt-get install -y python3-pip python-dev

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata

EXPOSE 80
EXPOSE 5000

COPY ./requirements.txt /application_root/requirements.txt

WORKDIR /application_root

RUN pip3 install -r requirements.txt

COPY . /application_root

ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
