FROM alpine:edge
MAINTAINER Norman Denayer<denayer.norman@gmail.com>

ADD . /landscape
WORKDIR /landscape

ENV FLASK_APP landscape
ENV APP_SETTINGS "config_prod"
ENV PYTHONPATH "/landscape"

RUN set -x && apk add --update python3 py3-lxml

RUN python3 -m pip install -r requirements.txt
RUN python3 setup.py install

RUN mkdir /data && touch /data/app.db

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]
EXPOSE 5000
VOLUME /data

