import discord
from discord.ext import commands, tasks
import pickle
import math
import random
import asyncio
from operator import attrgetter

listLen = 1000

class Labs(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.owner = None
        self.loading = True
        self.p_msg = []
        self.p_msg_grid = []
        self.p_msg_hybrid = []
        self.labs = {}
        self.mins = []
        self.helpString = "`^labs` - Request the list of Lab machines via DM\n\
`^quicklab` - Show a single ready lab machine\n\
`^labgrid` - Request a DM of Lab machine formatted in a grid.\n\
`^lablist` - Get a grid and a list of machines\n\
`^persistent` - (Administrator only) Generate a persistent (auto updating) message.\n\
`^persistentgrid` - (Administrator only) Generate a persistent (auto updating) grid message.\n\
`^persistentlist` - (Administrator only) Generate a persistent (auto updating) list message."
        try:
            in_labs = pickle.load( open ("./persistence/labsn.p", "rb" ) )
            #self.labs = in_labs[0]
            #self.mins = in_labs[1]
            pass
        except:
            pass
        

    
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.loadPMsg()
            print("Persistent messages successfully loaded.")
        except:
            print("Couldn't load persistent messages from file.")
        self.loading = False
        await self.bot.change_presence(activity=discord.Game(name="^labhelp"))
        appinfo = await self.bot.application_info()
        self.owner = appinfo.owner
    
    @commands.Cog.listener()
    async def on_message( self, message ):
        #Ignore own messages
        if message.author == self.bot.user:
            return
        if len(message.content) > 0:
            command = message.content.lower().split()[0]
        else:
            return
        if command[0] == "^":
            if command[1:] == "lablist":
                print( '{} asked for the lab machines'.format(message.author))
                labsString = self.getListStr() + self.getRLab()
                await message.author.send(self.getListStr())
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
            elif command[1:] == "labs":
                print( '{} asked for the lab hybrid machines'.format(message.author))
                labsString = self.getHybridStr()
                await message.author.send(labsString)
                if message.guild and message.channel.permissions_for(message.guild.me).send_messages:
                    await message.channel.send("Hybrid message of online lab machines DMed")
            elif self.loading:
                pass
            elif command[1:] == "persistentlist":
                print( '{} asked for a persistent message'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent message'.format(message.author))
                    labsString = self.getListStr() + "Quick Lab: " + self.getRLab()
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
                    self.p_msg_grid.append(await message.channel.send(self.getGridStr() + "Quick Lab: " + self.getRLab()))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
            elif command[1:] == "persistent":
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

    async def loadPMsg(self):
        self.pmsg = []
        self.p_msg_grid = []
        self.p_msg_hybrid = []
        msg_ids = pickle.load( open( "./persistence/pmsgn.p", "rb" ) )
        for msgt in msg_ids[0]:
            rmsg = None
            try:
                guild = self.bot.get_guild(msgt[0])
                channel = guild.get_channel(msgt[1])
                rmsg = await channel.fetch_message(msgt[2])
            except:
                continue
            if rmsg:
                self.p_msg.append(rmsg)
        for msgt in msg_ids[1]:
            rmsg = None
            try:
                guild = self.bot.get_guild(msgt[0])
                channel = guild.get_channel(msgt[1])
                rmsg = await channel.fetch_message(msgt[2])
            except:
                continue
            if rmsg:
                self.p_msg_grid.append(rmsg)
        for msgt in msg_ids[2]:
            rmsg = None
            try:
                guild = self.bot.get_guild(msgt[0])
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
    
    async def updatePMsg(self):
        labsString = f"{self.getListStr()}"
        #List message section
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except Exception as err:
                print("Problem editting persistent message. {}".format(err), flush=True)
        #Grid message section
        labsString = f"{self.getGridStr()}"
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=labsString, flush=True)
            except:
                print("Problem editting persistent message.", flush=True)
        labsString = f"{self.getHybridStr()}"
        #Hybrid message section
        for msg in self.p_msg_hybrid:
            try:
                await msg.edit(content=labsString, flush=True)
            except Exception as e:
                print(f"Problem editting persistent message. {e}", flush=True)
    
    def getListStr(self):
        labsString = ""
        for lab in sorted(self.labs.values(), key=attrgetter('users')):
            if lab.users != -1:
                labsString += "\n"+lab.host+" has "+str(lab.users)+" user"
                if lab.users != 1:
                    labsString += "s"
        labsString = "Available lab machines are:```c"+labsString
        labsString = labsString[:labsString[:listLen].rfind('\n')] + "\n```"
        return labsString

    def getGridStr(self):
        labsString = "Lab Machine Users By Room:\n```nim\n"
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
                    users = self.labs[host].users if host in self.labs.keys() else -1
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += "\n"
        return labsString + f"\n```\nQuick Lab: {self.getRLab()}\nQuick IP: {self.getRLabIP()}"
    
    def getHybridStr(self):
        labsString = "```nim\nLab Machine Users    -:- Average CPU load in last minute\n"
        
        sp = 2
        sp2 = 2
        for room in [218,219,220,221,232]:
            #Print Room Number
            labsString += f"lab{str(room)}:              -:- lab{str(room)}\n  "
            #Print Column Numbers
            for row in range(1,7):
                labsString += " 0" + str(row)
            labsString += " -:-  "
            for row in range(1,7):
                labsString += "  0" + str(row)
            labsString += "\n"
            #Print row letter and lab stats
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs[host].users if host in self.labs.keys() else -1
                    if users != -1:
                        labsString +=  f" {users: <2d}"
                    else:
                        labsString += "   "
                labsString += " -:- -" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs[host].load1min if host in self.labs.keys() else -1
                    labsString +=  f" {fpad(users)}"
                labsString += "\n"
        return labsString + f"\n```\nQuick Lab: {self.getRLab()}\nQuick IP: {self.getRLabIP()}"
    
    def getHybridStrOld(self):
        labsString = "```nim\nLab Machine Users By Room  -:- Quick Labs\n"
        
        labs = sorted(self.labs.values(), key=attrgetter('users'))
        ii = 0
        while ii < len(labs):
            if labs[ii].users == -1:
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
                labsString += " -:- " + labs[int(ii/2)].host + "\n  "
            else:
                labsString += " -:- IP: " + labs[int(ii/2)].ip + "\n  "
            ii = ii + 1
            for row in range(1,7):
                labsString += "  0" + str(row)
            if (ii % 2 == 0):
                labsString += " -:- " + labs[int(ii/2)].host + "\n"
            else:
                labsString += " -:- IP: " + labs[int(ii/2)].ip + "\n"
            ii = ii + 1
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs[host].users if host in self.labs.keys() else -1
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                if (ii % 2 == 0):
                    labsString += " -:- " + labs[int(ii/2)].host + "\n"
                else:
                    labsString += " -:- IP: " + labs[int(ii/2)].ip + "\n"
                ii = ii + 1
        return labsString + "\n```"

    def getRLab(self):
        return random.choice(self.mins).host

    def getRLabIP(self):
        return random.choice(self.mins).ip

    def getIP(self, hostname):
        if hostname in self.ips.keys():
            return self.ips[hostname]
        else:
            return "Unsupported"

def pad(inte,places):
    if inte < 1:
        padding = places-1
    else:
        padding = (places-int(1+math.log10(abs(inte))))
    return " " * padding

def fpad(flo):
    if flo == -1:
        return "   "
    else:
        return f"{flo:.1f}"