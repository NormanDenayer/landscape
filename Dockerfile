FROM alpine:edge
MAINTAINER Norman Denayer<denayer.norman@gmail.com>

ADD requirements.txt /landscape/
WORKDIR /landscape

ENV PYTHONPATH "/landscape"

RUN set -x && \
    apk add --no-cache python3 py3-lxml python3-dev musl-dev gcc ca-certificates tzdata && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    cp /usr/share/zoneinfo/Europe/Brussels /etc/localtime && \
    echo "Europe/Brussels" >  /etc/timezone && \
    apk del python3-dev musl-dev gcc tzdata && \
    rm -rf /var/cache/apk/*

ADD . /landscape
RUN set -x && \
    python3 setup.py install && \
    rm -vrf ~/.cache/pip

RUN mkdir /data
ENV LANDSCAPE_DB /data/app.db

CMD ["python3", "-m", "landscape.__init__"]
EXPOSE 5000
VOLUME /data
