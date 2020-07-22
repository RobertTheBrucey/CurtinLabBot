FROM python:3.8
RUN apt update && apt install -y openconnect
RUN apt install -y libffi-dev iptables expect bash git && pip install discord paramiko
RUN git clone https://github.com/RobertTheBrucey/CurtinLabBot.git && cp /CurtinLabBot/BotFiles/BotFiles/start.sh /start.sh && chmod +x /start.sh
CMD ["/start.sh"]
