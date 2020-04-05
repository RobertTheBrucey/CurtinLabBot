FROM python:3-alpine
RUN apk add openconnect --no-cache  --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted
RUN apk add build-base libffi-dev iptables expect bash && apk del libressl-dev \
&& apk add openssl-dev && pip install discord paramiko
ADD start.sh /start.sh
RUN chmod +x /start.sh
COPY BotFiles /BotFiles

CMD ["/start.sh"]