FROM python:3-alpine
MAINTAINER Norman Denayer<denayer.norman@gmail.com>

ADD . /landscape
WORKDIR /landscape

RUN set -x && apk add --update postgresql-dev gcc python3-dev musl-dev

RUN pip install -r requirements.txt
RUN APP_SETTINGS="config_dev" python setup.py install

ENV FLASK_APP landscape
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
EXPOSE 5000
