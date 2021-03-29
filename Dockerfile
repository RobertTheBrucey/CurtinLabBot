FROM python:3.8
RUN apt update && apt upgrade -y && apt install -y bash git
COPY src/requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt
COPY . /
WORKDIR /src
RUN chmod +x start.sh
CMD [ "./start.sh" ]