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

listLen = 1000
class BotClient( discord.Client ):
    
    def __init__(self, configfile):
        super().__init__()
        self.labs = {}
        self.p_msg = []
        self.p_msg_grid = []
        self.mins = []
        self.loading = True
        self.helpString = "`^labs` - Request the list of Lab machines via DM\n`^quicklab` - Show a single ready lab machine\n`^labgrid` - Request a DM of Lab machine formatted in a grid.\n`^persistent` - (Administrator only) Generate a persistent (auto updating) message.\n`^persistentgrid` - (Administrator only) Generate a persistent (auto updating) grid message.\n`^labhybrid` - Get a grid and a list of machines"
        self.configfile = configfile
        self.owner = None
        try:
            labt = pickle.load( open( "./persistence/labs.p", "rb" ) )
            self.labs = labt[0]
            self.mins = labt[1]
            print("Labs successfully loaded.")
        except:
            print("No labs to load")

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
        #asyncio.ensure_future(self.pollLabs())

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
            elif command[1:] == "labhybrid":
                print( '{} asked for the lab hybrid machines'.format(message.author))
                labsString = self.getHybridStr()
                await message.author.send(labsString)
                try:
                    await message.channel.send("Hybrid message of online lab machines DMed")
                except:
                    print("Couldn't send message to channel.")
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
    
    def getHybridStr(self):
        labsString = "```yaml\nLab Machine Users By Room  -:- Quick Labs\n"
        labs = sorted(self.labs,key=self.labs.get)
        ii = 0
        while ii < len(labs):
            if self.labs[labs[ii]] == -1:
                labs.remove(labs[ii])
            else:
                ii = ii + 1
        for i in range(len(labs),31):
            labs.append("")
        ii = 0
        sp = 2
        for room in [218,219,220,221,232]:
            labsString += "lab" + str(room) + ":                   "
            labsString += " -:- " + labs[ii] + "\n  "
            ii = ii + 1
            for row in range(1,7):
                labsString += "  0" + str(row)
            labsString += " -:- " + labs[ii] + "\n"
            ii = ii + 1
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += " -:- " + labs[ii] + "\n"
                ii = ii + 1
        return labsString + "\n```"

    async def getFromQ(self, q):
        try:
            users = q.get(timeout=2)
        except:
            users = -1
        return users

    async def pollLabs(self):
        sp = 2
        creds = config.getCreds(self.configfile)
        logfile = "./persistence/"+config.getLogfile(self.configfile)
        keyfile = "./persistence/"+config.getKeyfile(self.configfile)
        while True:
            print("Starting scan at {}".format(str(datetime.datetime.now())))
            mini = 100
            mins = []
            for room in [218,219,220,221,232]:
                print("lab" + str(room) + ":\n  ", end='')
                for row in range(1,7):
                    print( "  0" + str(row), end='')
                print("")
                for column in "abcd":
                    print("-" + str(column), end='')
                    for row in range(1,7):
                        try:
                            users = -1
                            host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                            q = Queue()
                            proc = Process(target=checkLab, args=(host,q,creds,keyfile))
                            proc.start()
                            try:
                                await asyncio.sleep(2)
                                users = q.get(timeout=0)
                                proc.join()
                            except Exception as err:
                                try:
                                    proc.terminate()
                                except:
                                    pass
                            self.labs[host] = users
                            if (users>-1 and users < mini):
                                mini = users
                                mins = []
                            if (users == mini):
                                mins.append(host)
                            print("  " + str((" ",users)[users!=-1]) + pad(users,sp), end = '')
                            await asyncio.sleep(1) #Crashes here somehow?
                        except:
                            pass
                    print("")
            self.mins = mins
            print("Finishing scan at {}".format(str(datetime.datetime.now())), flush=True)
            max = -1
            for lab in sorted(self.labs,key=self.labs.get):
                if self.labs[lab] > max:
                    max = self.labs[lab]
            if max == -1:
                print("All labs down, loading from backup", flush=True)
                labt = pickle.load( open( "./persistence/labs.p", "rb" ) )
                self.labs = labt[0]
                self.mins = labt[1]
            else:
                print("Saving up machines to file", flush=True)
                pickle.dump( (self.labs,self.mins), open("./persistence/labs.p", "wb" ) )
            logStr = ""
            if os.path.isfile(logfile):
                print("Log file exists, appending", flush=True)
                logStr += "{},".format(str(datetime.datetime.now()))+","
                for lab in sorted(self.labs.keys()):
                    logStr += str(self.labs[lab]) + ","
                logStr = logStr[:-1]
            elif not os.path.isdir(logfile):
                print("Log file specified but none existant, creating", flush=True)
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
                        print("Log file successfully written to.", flush=True)
                except:
                    print("Log file unable to be written to", flush=True)
            else:
                print("Log file not specified", flush=True)
            await asyncio.sleep(1)
            await self.updatePMsg()
            await asyncio.sleep(300)

    async def updatePMsg(self):
        labsString = self.getListStr() + "This list is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except Exception as err:
                print("Problem editting persistent message. {}".format(err), flush=True)
        #Grid message section
        labsString = self.getGridStr()
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=(labsString + "This grid is updated every 10 minutes.\nQuick Lab: " + random.choice(self.mins)), flush=True)
            except:
                print("Problem editting persistent message.", flush=True)

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

    async def savePMsg(self):
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