import discord
import asyncio
#import base64
import paramiko
import re
import datetime
#import copy
import pickle
import math
import random
import os.path
from multiprocessing import Process, Queue
import config

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
        self.owner = None
        try:
            self.labs = pickle.load( open( "./persistence/labs.p", "rb" ) )
            labt = pickle.load( open( "./persistence/labsn.p", "rb" ) )
            self.labs = labt[0]
            self.mins = labt[1]
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
        appinfo = await self.application_info()
        self.owner = appinfo.owner

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
                labsString = self.getListStr() + random.choice(self.mins)
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
                lab = random.choice(self.mins)
                try:
                    await message.channel.send("Quick Lab: {}".format(lab))
                except:
                    await message.author.send("Quick Lab: {}".format(lab))
            elif command[1:] == "labhelp":
                print( '{} asked for the lab help'.format(message.author))
                try:
                    await message.channel.send(self.helpString)
                except:
                    await message.author.send(self.helpString)
            elif command[1:] == "restart":
                if message.author == self.owner:
                    await message.author.send("Restarting...")
                    exit()
            elif self.loading:
                pass
            elif command[1:] == "persistent":
                print( '{} asked for a persistent message'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent message'.format(message.author))
                    labsString = self.getListStr() + "This list is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)
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

    def getListStr(self):
        labsString = ""
        for lab in sorted(self.labs,key=self.labs.get):
            if self.labs[lab] != -1:
                labsString += "\n"+lab+" has "+str(self.labs[lab])+" user"
                if self.labs[lab] != 1:
                    labsString += "s"
        labsString = "Available lab machines are:```c"+labsString
        labsString = labsString[:labsString[:listLen].rfind('\n')] + "\n```"
        return labsString

    def getGridStr(self):
        labsString = "Lab Machine Users By Room:\n```yaml\n"
        sp = 2
        for room in [218,219,220,221,232]:
            labsString += "lab" + str(room) + ":\n  "
            for row in range(1,7):
                labsString += "  0" + str(row)
            labsString += "\n"
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += "\n"
        return labsString + "\n```"

    async def getFromQ(self, q):
        try:
            users = q.get(timeout=2)
        except:
            users = -1
        return users

    async def pollLabs(self):
        creds = config.getCreds(self.configfile)
        logfile = "./persistence/"+config.getLogfile(self.configfile)
        keyfile = "./persistence/"+config.getKeyfile(self.configfile)
        while True:
            print("Starting scan at {}".format(str(datetime.datetime.now())))
            mini = 100
            mins = []
            for room in [218,219,220,221,232]:
                for column in "abcd":
                    for row in range(1,7):
                        users = -1
                        host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                        print(host+": ", end = '')
                        q = Queue()
                        proc = Process(target=checkLab, args=(host,q,creds,keyfile))
                        proc.start()
                        try:
                            users = q.get(timeout=2)
                            #users = await self.getFromQ(q)
                            proc.join()
                            if users != -1:
                                print(str(users) + " Users.")
                            else:
                                print("Down")
                        except Exception as err:
                            print("Down")
                            proc.terminate()
                        self.labs[host] = users
                        if (users>-1 and users < mini):
                            mini = users
                            mins = []
                        if (users == mini):
                            self.mins.append(host)
                        await asyncio.sleep(0.1)
            self.mins = mins
            print("Finishing scan at {}".format(str(datetime.datetime.now())))
            max = -1
            for lab in sorted(self.labs,key=self.labs.get):
                if self.labs[lab] > max:
                    max = self.labs[lab]
            if max == -1:
                print("All labs down, loading from backup")
                labt = pickle.load( open( "./persistence/labsn.p", "rb" ) )
                self.labs = labt[0]
                self.mins = labt[1]
            else:
                print("Saving up machines to file")
                pickle.dump( (self.labs,self.mins), open ("./persistence/labs.p", "wb" ) )
            await self.updatePMsg()
            logStr = ""
            if os.path.isfile(logfile):
                print("Log file exists, appending")
                logStr += "{},".format(str(datetime.datetime.now()))+","
                for lab in sorted(self.labs.keys()):
                    logStr += str(self.labs[lab]) + ","
                logStr = logStr[:-1]
            elif not os.path.isdir(logfile):
                print("Log file specified but none existant, creating")
                dataStr = "{},".format(str(datetime.datetime.now()))
                logStr += "Time,"
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
            await asyncio.sleep(5)
            await asyncio.sleep(300)

    async def updatePMsg(self):
        labsString = self.getListStr() + "This list is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)
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
        msg_ids = pickle.load( open( "./persistence/pmsgn.p", "rb" ) )
        for msgt in msg_ids[0]:
            rmsg = None
            try:
                guild = self.get_guild(msgt[0])
                channel = guild.get_channel(msgt[1])
                rmsg = await channel.fetch_message(msgt[2])
            except:
                continue
            if rmsg:
                self.p_msg.append(rmsg)
        for msgt in msg_ids[1]:
            rmsg = None
            try:
                guild = self.get_guild(msgt[0])
                channel = guild.get_channel(msgt[1])
                rmsg = await channel.fetch_message(msgt[2])
            except:
                continue
            if rmsg:
                self.p_msg_grid.append(rmsg)
        print(str(len(self.p_msg)) + " persistent messages loaded and "+ str(len(self.p_msg_grid)) +" persistent grids loaded")
        #Legacy loading
        """ msg_ids = pickle.load( open( "./persistence/pmsg.p", "rb" ) )
        for msgt in msg_ids[0]:
            rmsg = None
            channels = self.get_all_channels()
            for channel in channels:
                try:
                    rmsg = await channel.fetch_message(msgt)
                except:
                    continue
            if rmsg:
                if rmsg not in self.p_msg:
                    self.p_msg.append(rmsg)
        for msgt in msg_ids[1]:
            rmsg = None
            channels = self.get_all_channels()
            for channel in channels:
                try:
                    rmsg = await channel.fetch_message(msgt)
                except:
                    continue
            if rmsg:
                if rmsg not in self.p_msg_grid:
                    self.p_msg_grid.append(rmsg)
        print(str(len(self.p_msg)) + " persistent messages loaded and "+ str(len(self.p_msg_grid)) +" persistent grids loaded") """

    async def savePMsg(self):
        #Legacy saving
        """ msg_ids = []
        grid_msg_ids = []
        for msg in self.p_msg:
            msg_ids.append(msg.id)
        for msg in self.p_msg_grid:
            grid_msg_ids.append(msg.id)
        msgs = (msg_ids,grid_msg_ids)
        pickle.dump( msgs, open ("./persistence/pmsg.p", "wb" ) ) """
        msg_ids = []
        grid_msg_ids = []
        for msg in self.p_msg:
            msg_ids.append((msg.guild.id,msg.channel.id,msg.id))
        for msg in self.p_msg_grid:
            grid_msg_ids.append((msg.guild.id,msg.channel.id,msg.id))
        msgs = (msg_ids,grid_msg_ids)
        pickle.dump( msgs, open ("./persistence/pmsgn.p", "wb" ) )
    
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
            if match:
                users = int(match.group(1))
                if users > 0:
                    users = users-1
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