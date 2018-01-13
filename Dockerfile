FROM alpine:edge
MAINTAINER Norman Denayer<denayer.norman@gmail.com>

ADD . /landscape
WORKDIR /landscape

ENV FLASK_APP landscape
ENV APP_SETTINGS "config_prod"
ENV PYTHONPATH "/landscape"

RUN set -x && \
    apk add --update python3 py3-lxml python3-dev musl-dev gcc ca-certificates && \
    python3 -m pip install -r requirements.txt && \
    python3 setup.py install && \
    apk del python3-dev musl-dev gcc

ENV START_BACKGROUND "y"
RUN mkdir /data && touch /data/app.db

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000", "--with-threads"]
EXPOSE 5000
VOLUME /data
