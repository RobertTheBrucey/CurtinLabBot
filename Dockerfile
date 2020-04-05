FROM python:3-alpine
RUN apk add openconnect --no-cache  --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted
RUN apk add build-base libffi-dev iptables expect && pip install discord paramiko
ADD start.sh /
COPY BotFiles/* /BotFiles

CMD ["/start.sh"]