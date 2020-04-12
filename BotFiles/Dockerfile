FROM python:3-alpine
RUN apk add openconnect --no-cache  --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --allow-untrusted
RUN apk add build-base libffi-dev iptables expect bash git && apk del libressl-dev \
&& apk add openssl-dev && pip install discord paramiko
RUN git clone https://github.com/RobertTheBrucey/CurtinLabBot.git && cp CurtinLabBot/BotFiles/start.sh /start.sh && chmod +x /start.sh
#ADD BotFiles/start.sh /start.sh
#RUN chmod +x /start.sh
#COPY BotFiles /BotFiles

CMD ["/start.sh"]