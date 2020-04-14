if __name__ == '__main__':
    import discord
    import botClient as bc
    from config import getToken,getCreds
    import sys

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
    #Store lab, current count and mins?
    labs = [{},[]]
    #Store persistent messages, with type (message,channel,guild,type)
    pmsg = []
    #Thread 1 pls
    client = bc.BotClient(configfile)
    client.run(getToken(filename=configfile))
    #Thread 2 pls
    print("Program End?")