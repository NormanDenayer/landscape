FROM alpine:edge
MAINTAINER Norman Denayer<denayer.norman@gmail.com>

ADD requirements.txt /landscape/
WORKDIR /landscape

ENV PYTHONPATH "/landscape"

RUN set -x && \
    apk add --update python3 py3-lxml python3-dev musl-dev gcc ca-certificates && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    apk del python3-dev musl-dev gcc

ADD . /landscape
RUN set -x && \
    python3 setup.py install && \
    rm -vrf ~/.cache/pip

RUN mkdir /data && touch /data/app.db

CMD ["python3", "-m", "landscape.__init__"]
EXPOSE 5000
VOLUME /data
