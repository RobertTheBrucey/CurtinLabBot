if __name__ == '__main__':
    import discord
    import botClient as bc
    from config import getToken,getCreds
    import sys
    import threading
    import labScan as ls
    import logging
    import datetime

    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename='./persistence/discord'+str(datetime.datetime.now())+'.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    if len(sys.argv) < 2:
        configfile = "./persistence/config.ini"
    else:
        configfile = sys.argv[1]

    try:
        getToken(filename=configfile)
        getCreds(filename=configfile)
    except:
        print("Config file invalid, creating a new one")
        base = "[token]\n\
token=\n\n\
[creds]\n\
username=\n\
password=\n\n\
Password is optional if using keyfile\n\
[logging]\n\
logfile=\n\n\
[keyfile]\n\
keyfile=\n\n\
[ownerid]\n\
ownerid="
        file = open("config.ini", "w")
        file.write(base)
        file.close()
        exit()

    """ Setup """
  
    #Thread 1 pls
    scanner = ls.LabScan(configfile=configfile)
    scanT = threading.Thread(target=scanner.pollLabs, daemon=True)
    scanT.start()
    #Thread 2 pls
    client = bc.BotClient(configfile,scanner)
    client.run(getToken(filename=configfile))
    print("Bot Exitting For No Reason")