import discord
import asyncio
import paramiko
import re
import datetime
import pickle
import math
import random
import os.path
from multiprocessing import Process, Queue
import config
import socket
import sys

listLen = 1000
class BotClient( discord.Client ):
    
    def __init__(self, configfile, scanner):
        super().__init__()
        self.scanner = scanner
        self.scanner.bot = self
        self.p_msg = []
        self.p_msg_grid = []
        self.p_msg_hybrid = []
        self.loading = True
        self.helpString = "`^labs` - Request the list of Lab machines via DM\n`^quicklab` - Show a single ready lab machine\n`^labgrid` - Request a DM of Lab machine formatted in a grid.\n`^persistent` - (Administrator only) Generate a persistent (auto updating) message.\n`^persistentgrid` - (Administrator only) Generate a persistent (auto updating) grid message.\n`^labhybrid` - Get a grid and a list of machines\n`^persistenthybrid` - (Administrator only) Generate a persistent (auto updating) hybrid message."
        self.configfile = configfile
        self.owner = None
        self.eloop = None

    async def on_ready( self ):
        print( 'Logged on as {0}!'.format( self.user ) )
        await self.change_presence(activity=discord.Game(name="Loading..."))
        #for guild in self.guilds:
        #    print(guild)
        #    for member in guild.members:
        #        print("  ",member)
        try:
            await self.loadPMsg()
            print("Persistent messages successfully loaded.")
        except:
            print("Couldn't load persistent messages from file.")
        self.loading = False
        await self.change_presence(activity=discord.Game(name="^labhelp"))
        appinfo = await self.application_info()
        self.owner = appinfo.owner
        self.eloop = asyncio.get_event_loop()
        #asyncio.get_event_loop().create_task(self.checkForNew())

    async def checkForNew(self):
        while True:
            if self.scanner.newLabs:
                await asyncio.sleep(1)
                await self.updatePMsg()
                self.scanner.newLabs = False
            await asyncio.sleep(1)

    async def on_message( self, message ):
        #Ignore own messages
        if message.author == self.user:
            return
        if len(message.content) > 0:
            command = message.content.lower().split()[0]
        else:
            return
        if command[0] == "^":
            if command[1:] == "labs":
                print( '{} asked for the lab machines'.format(message.author))
                labsString = self.getListStr() + self.getRLab()
                await message.author.send(labsString)
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send("List of online lab machines DMed\nQuick machine: {}".format(lab))
            elif command[1:] == "labgrid":
                print( '{} asked for the lab machine grid'.format(message.author))
                await message.author.send(self.getGridStr())
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send("Grid DMed to you")
            elif command[1:] == "quicklab":
                print( '{} asked for a quick lab'.format(message.author))
                lab = self.getRLab()
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send("Quick Lab: {}".format(lab))
                else:
                    await message.author.send("Quick Lab: {}".format(lab))
            elif command[1:] == "labhelp":
                print( '{} asked for the lab help'.format(message.author))
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send(self.helpString)
                else:
                    await message.author.send(self.helpString)
            elif command[1:] == "restart":
                if message.author == self.owner:
                    await message.author.send("Restarting...")
                    print("Restart requested")
                    sys.exit()
            elif command[1:] == "labhybrid":
                print( '{} asked for the lab hybrid machines'.format(message.author))
                labsString = self.getHybridStr()
                await message.author.send(labsString)
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send("Hybrid message of online lab machines DMed")
            elif self.loading:
                pass
            elif command[1:] == "persistent":
                print( '{} asked for a persistent message'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent message'.format(message.author))
                    labsString = self.getListStr() + "This list is updated every 10 minutes.\nQuick Lab: " + self.getRLab()
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
                    self.p_msg_grid.append(await message.channel.send(self.getGridStr() + "This grid is updated every 10 minutes.\nQuick Lab: " + self.getRLab()))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
            elif command[1:] == "persistenthybrid":
                print( '{} asked for a persistent hybrid grid'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent hybrid'.format(message.author))
                    for msg in self.p_msg_hybrid:
                        if msg.channel == message.channel:
                            self.p_msg_hybrid.remove(msg)
                    self.p_msg_hybrid.append(await message.channel.send(self.getHybridStr()))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
        if self.scanner.newLabs:
            await self.updatePMsg()
            self.scanner.newLabs = False

    def getListStr(self):
        labsString = ""
        self.scanner.lock.acquire()
        for lab in sorted(self.scanner.labs,key=self.scanner.labs.get):
            if self.scanner.labs[lab] != -1:
                labsString += "\n"+lab+" has "+str(self.scanner.labs[lab])+" user"
                if self.scanner.labs[lab] != 1:
                    labsString += "s"
        self.scanner.lock.release()
        labsString = "Available lab machines are:```c"+labsString
        labsString = labsString[:labsString[:listLen].rfind('\n')] + "\n```"
        return labsString

    def getGridStr(self):
        labsString = "Lab Machine Users By Room:\n```yaml\n"
        sp = 2
        self.scanner.lock.acquire()
        for room in [218,219,220,221,232]:
            labsString += "lab" + str(room) + ":\n  "
            for row in range(1,7):
                labsString += "  0" + str(row)
            labsString += "\n"
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.scanner.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += "\n"
        self.scanner.lock.release()
        return labsString + "\n```"
    
    def getHybridStr(self):
        labsString = "```yaml\nLab Machine Users By Room  -:- Quick Labs\n"
        self.scanner.lock.acquire()
        labs = sorted(self.scanner.labs,key=self.scanner.labs.get)
        ii = 0
        while ii < len(labs):
            if self.scanner.labs[labs[ii]] == -1:
                labs.remove(labs[ii])
            else:
                ii = ii + 1
        for i in range(len(labs),15):
            labs.append("")
        ii = 0
        sp = 2
        for room in [218,219,220,221,232]:
            labsString += "lab" + str(room) + ":                   "
            if (ii % 2 == 0):
                labsString += " -:- " + labs[int(ii/2)] + "\n  "
            else:
                labsString += " -:- IP: " + getIP(labs[int(ii/2)]) + "\n  "
            ii = ii + 1
            for row in range(1,7):
                labsString += "  0" + str(row)
            if (ii % 2 == 0):
                labsString += " -:- " + labs[int(ii/2)] + "\n"
            else:
                labsString += " -:- IP: " + getIP(labs[int(ii/2)]) + "\n"
            ii = ii + 1
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.scanner.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                if (ii % 2 == 0):
                    labsString += " -:- " + labs[int(ii/2)] + "\n"
                else:
                    labsString += " -:- IP: " + getIP(labs[int(ii/2)]) + "\n"
                ii = ii + 1
        self.scanner.lock.release()
        return labsString + "\n```"

    async def updatePMsg(self):
        labsString = self.getListStr() + "This list is updated every 10 minutes.\nQuick Lab: " + self.getRLab()
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except Exception as err:
                print("Problem editting persistent message. {}".format(err), flush=True)
        #Grid message section
        labsString = self.getGridStr() + "This grid is updated every 10 minutes.\nQuick Lab: " + self.getRLab()
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=labsString, flush=True)
            except:
                print("Problem editting persistent message.", flush=True)
        labsString = self.getHybridStr() + "This grid is updated every 10 minutes.\nQuick Lab: " + self.getRLab()
        for msg in self.p_msg_hybrid:
            try:
                await msg.edit(content=labsString, flush=True)
            except:
                print("Problem editting persistent message.", flush=True)

    async def loadPMsg(self):
        self.pmsg = []
        self.p_msg_grid = []
        self.p_msg_hybrid = []
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
        for msgt in msg_ids[2]:
            rmsg = None
            try:
                guild = self.get_guild(msgt[0])
                channel = guild.get_channel(msgt[1])
                rmsg = await channel.fetch_message(msgt[2])
            except:
                continue
            if rmsg:
                self.p_msg_hybrid.append(rmsg)
        print(str(len(self.p_msg)) + " persistent messages loaded, "+ str(len(self.p_msg_grid)) +" persistent grids loaded and "+ str(len(self.p_msg_hybrid))+" hybrid messages loaded.")

    async def savePMsg(self):
        msg_ids = []
        grid_msg_ids = []
        hybrid_msg_ids = []
        for msg in self.p_msg:
            msg_ids.append((msg.guild.id,msg.channel.id,msg.id))
        for msg in self.p_msg_grid:
            grid_msg_ids.append((msg.guild.id,msg.channel.id,msg.id))
        for msg in self.p_msg_hybrid:
            hybrid_msg_ids.append((msg.guild.id,msg.channel.id,msg.id))
        msgs = (msg_ids,grid_msg_ids,hybrid_msg_ids)
        pickle.dump( msgs, open ("./persistence/pmsgn.p", "wb" ) )

    def getRLab(self):
        self.scanner.lock.acquire()
        lab = random.choice(self.scanner.mins)
        self.scanner.lock.release()
        return lab
    
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

def getIP(hostname):
    return socket.gethostbyname(hostname)