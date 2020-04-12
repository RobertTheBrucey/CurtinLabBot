import discord
import asyncio
import base64
import paramiko
import re
import datetime
import copy
import pickle
import math
import random
import os.path
from multiprocessing import Process, Queue
import config

#Todo: Persistent messages
#Grid view

reserved = ['simpintro','simp','unsimp','unsimpall']
listLen = 1000;
class BotClient( discord.Client ):
    
    def __init__(self, configfile):
        super().__init__()
        self.labs = {}
        self.p_msg = []
        self.p_msg_grid = []
        self.mins = []
        self.loading = True
        self.helpString = "`^labs` - Request the list of Lab machines via DM\n`^quicklab` - Show a single ready lab machine\n`^labgrid` - Request a DM of Lab machine formatted in a grid.\n`^persistent` - (Administrator only) Generate a persistent (auto updating) message.\npersistentgrid - (Administrator only) Generate a persistent (auto updating) grid message."
        self.configfile = configfile
        try:
            self.labs = pickle.load( open( "./persistence/labs.p", "rb" ) )
            print("Labs successfully loaded.")
        except:
            print("No labs to load")
        asyncio.get_event_loop().create_task(self.pollLabs())

    async def on_ready( self ):
        print( 'Logged on as {0}!'.format( self.user ) )
        await self.change_presence(activity=discord.Game(name="Loading..."))
        try:
            await self.loadPMsg()
            print("Persistent messages successfully loaded.")
        except:
            print("Couldn't load persistent messages from file.")
        await self.updatePMsg()
        self.loading = False
        await self.change_presence(activity=discord.Game(name="^labhelp"))

    async def on_message( self, message ):
        #Ignore own messages
        if message.author == self.user:
            return
        if len(message.content) > 0:
            command = message.content.lower().split()[0]
        else:
            command = " "
        if command[0] == "^":
            if command[1:] == "labs":
                print( '{} asked for the lab machines'.format(message.author))
                labsString = ""
                first = ""
                for lab in sorted(self.labs,key=self.labs.get):
                    if self.labs[lab] != -1:
                        if first == "":
                            first = lab
                        #labsString += "\n{} has {} user{}".format((lab,str(self.labs[lab])),("","s")[self.labs[lab]==1])
                        labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
                labsString = "Available lab machines are:```"+labsString
                labsString = labsString[:labsString[:listLen].rfind('\n')] + "```"
                await message.author.send(labsString)
                try:
                    await message.channel.send("List of online lab machines DMed\nQuick machine: {}".format(first))
                except:
                    print("Couldn't send message to channel.")
            elif command[1:] == "labgrid":
                print( '{} asked for the lab machine grid'.format(message.author))
                await message.author.send(self.getGridStr())
                try:
                    await message.channel.send("Grid DMed to you")
                except:
                    print("Couldn't  send message to channel.")
            elif command[1:] == "quicklab":
                print( '{} asked for a quick lab'.format(message.author))
                for lab in sorted(self.labs,key=self.labs.get):
                    try:
                        await message.channel.send("Quick Lab: {}".format(lab))
                    except:
                        await message.author.send("Quick Lab: {}".format(lab))
                    break
            elif command[1:] == "labhelp":
                print( '{} asked for the lab help'.format(message.author))
                try:
                    await message.channel.send(self.helpString)
                except:
                    await message.channel.send(self.helpString)
            elif self.loading:
                pass
            elif command[1:] == "persistent":
                print( '{} asked for a persistent message'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent message'.format(message.author))
                    labsString = ""
                    for lab in sorted(self.labs,key=self.labs.get):
                        if self.labs[lab] != -1:
                            labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
                    labsString = "Available lab machines are:```"+labsString
                    labsString = labsString[:labsString[:listLen].rfind('\n')] + "```This list is updated every 10 minutes."
                    for msg in self.p_msg:
                        if msg.channel == message.channel:
                            self.p_msg.remove(msg)
                    self.p_msg.append(await message.channel.send(labsString))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
            elif command[1:] == "persistentgrid":
                print( '{} asked for a persistent lab machine grid'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent grid'.format(message.author))
                    for msg in self.p_msg_grid:
                        if msg.channel == message.channel:
                            self.p_msg_grid.remove(msg)
                    self.p_msg_grid.append(await message.channel.send(self.getGridStr() + "This grid is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
    def getGridStr(self):
        labsString = "Lab Machine Users By Room:\n```\n"
        sp = 2
        self.mins = []
        mini = 100
        for room in [218,219,220,221,232]:
            labsString += "lab" + str(room) + "\n  "
            for row in range(1,7):
                labsString += "  0" + str(row)
            labsString += "\n"
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs.get(host,-1)
                    if (users>-1 and users < mini):
                        mini = users
                        self.mins = []
                    if (users == mini):
                        self.mins.append(host)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += "\n"
        return labsString + "```"

    async def pollLabs(self):
        creds = config.getCreds(self.configfile)
        logfile = "./persistence/"+config.getLogfile(self.configfile)
        keyfile = "./persistence/"+config.getKeyfile(self.configfile)
        while True:
            print("Starting scan at {}".format(str(datetime.datetime.now())))
            for room in [218,219,220,221,232]:
                for column in "abcd":
                    for row in range(1,7):
                        users = -1
                        host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                        #print("\033[1A"+host+": ", end = '')
                        print(host+": ", end = '')
                        q = Queue()
                        #print("step 1")
                        proc = Process(target=checkLab, args=(host,q,creds,keyfile))
                        #print("step 2")
                        proc.start()
                        #print("step 3")
                        try:
                            #print("Proc Join")
                            #proc.join(timeout=5)
                            #print("get queue")
                            users = q.get(timeout=2)
                            proc.join()
                            print(str(users) + " Users.")
                        except Exception as err:
                            print("Down")
                            proc.terminate()
                            #print(type(err))
                        #print("step 4")
                        self.labs[host] = users
                        #print("End of thingy")
                        await asyncio.sleep(1)
            print("Finishing scan at {}".format(str(datetime.datetime.now())))
            max = -1
            for lab in sorted(self.labs,key=self.labs.get):
                if self.labs[lab] > max:
                    max = self.labs[lab]
            if max == -1:
                print("All labs down, loading from backup")
                self.labs = pickle.load( open( "./persistence/labs.p", "rb" ) )
            else:
                print("Saving up machines to file")
                pickle.dump( self.labs, open ("./persistence/labs.p", "wb" ) )
            await self.updatePMsg()
            logStr = ""
            if os.path.isfile(logfile):
                print("Log file exists, appending")
                for lab in sorted(self.labs.keys()):
                    logStr += str(self.labs[lab]) + ","
                logStr = logStr[:-1]
            elif not os.path.isdir(logfile):
                print("Log file specified but none existant, creating")
                dataStr = ""
                for lab in sorted(self.labs.keys()):
                    logStr += lab.split(".")[0][3:] + ","
                    dataStr += str(self.labs[lab]) + ","
                logStr = logStr[:-1] + "\n" + dataStr[:-1]
            if not logStr == "":
                try:
                    with open(logfile,"a") as f:
                        f.write(logStr+"\n")
                        print("Log file successfully written to.")
                except:
                    print("Log file unable to be written to")
            else:
                print("Log file not specified")
            await asyncio.sleep(300)
            #a = False

    async def updatePMsg(self):
        labsString = ""
        for lab in sorted(self.labs,key=self.labs.get):
            if self.labs[lab] != -1:
                labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
        labsString = "Available lab machines are:```"+labsString
        labsString = labsString[:labsString[:listLen].rfind('\n')] + "```This list is updated every 10 minutes."
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except:
                print("Problem editting persistent message.")
        #Grid message section
        labsString = self.getGridStr()
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=(labsString + "This grid is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)))
            except:
                print("Problem editting persistent message.")

    async def loadPMsg(self):
        self.pmsg = []
        self.p_msg_grid = []
        msg_ids = pickle.load( open( "./persistence/pmsg.p", "rb" ) )
        for msg in msg_ids[0]:
            #print("Attempting to load id " + str(msg))
            rmsg = None
            channels = self.get_all_channels()
            for channel in channels:
                #print("Checking channel: " + str(channel))
                try:
                    rmsg = await channel.fetch_message(msg)
                except:
                    continue
            if rmsg:
                self.p_msg.append(rmsg)
        for msg in msg_ids[1]:
            #print("Attempting to load id " + str(msg))
            rmsg = None
            channels = self.get_all_channels()
            for channel in channels:
                #print("Checking channel: " + str(channel))
                try:
                    rmsg = await channel.fetch_message(msg)
                except:
                    continue
            if rmsg:
                self.p_msg_grid.append(rmsg)
        #print("{} persistent messages loaded and {} persistent grids loaded" % (str(len(self.p_msg)),str(len(self.p_msg_grid))))
        print(str(len(self.p_msg)) + " persistent messages loaded and "+ str(len(self.p_msg_grid)) +" persistent grids loaded")

    async def savePMsg(self):
        msg_ids = []
        grid_msg_ids = []
        for msg in self.p_msg:
            msg_ids.append(msg.id)
        for msg in self.p_msg_grid:
            grid_msg_ids.append(msg.id)
        msgs = (msg_ids,grid_msg_ids)
        pickle.dump( msgs, open ("./persistence/pmsg.p", "wb" ) )
    
def checkLab( host, temp, creds, keyfile ):
    sshclient = paramiko.SSHClient()
    sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
        sshclient.connect(host, username=creds[0], password=creds[1], timeout=1, banner_timeout=1, auth_timeout=1, key_filename=keyfile)
        stdin, stdout, stderr = sshclient.exec_command('w',timeout=1)
        for line in stderr:
            #print(line.strip('\n'))
            pass
        for line in stdout:
            #print(line.strip('\n'))
            match = re.search(r"(\d+)(?: users?,)",line)
            #print(match)
            if match:
                users = int(match.group(1))
                if users > 0:
                    users = users-1
                #print("Users: {}".format(users))
                temp.put(users)
                break
        sshclient.close()
    except:
        pass

def pad(inte,places):
    if inte < 1:
        padding = places-1
    else:
        padding = (places-int(1+math.log10(abs(inte))))
    return " " * padding