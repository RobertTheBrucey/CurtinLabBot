#!/bin/bash
( echo yes; echo $ANYCONNECT_PASSWORD ) | openconnect $ANYCONNECT_SERVER --user=$ANYCONNECT_USER --timestamp
#echo $ANYCONNECT_PASSWORD|openconnect $ANYCONNECT_SERVER --user=$ANYCONNECT_USER --server-cert -b

#sleep 5

#iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE
#iptables -A FORWARD -i eth0 -j ACCEPT

#route del -net 172.17.0.0 netmask 255.255.240.0  dev tun0

echo $ANYCONNECT_PASSWORD $ANYCONNECT_USER $ANYCONNECT_SERVER

ping lab219-b06.cs.curtin.edu.au.
cd BotFiles
while true;do
python3 CurtinLabBot.py
done