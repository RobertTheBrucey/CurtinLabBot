import discord
from discord.ext import commands, tasks
import pickle
import math
import aiohttp
import random

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
        self.ips = {}
        self.mins = []
        self.helpString = "`^labs` - Request the list of Lab machines via DM\n\
`^quicklab` - Show a single ready lab machine\n\
`^labgrid` - Request a DM of Lab machine formatted in a grid.\n\
`^lablist` - Get a grid and a list of machines\n\
`^persistent` - (Administrator only) Generate a persistent (auto updating) message.\n\
`^persistentgrid` - (Administrator only) Generate a persistent (auto updating) grid message.\n\
`^persistentlist` - (Administrator only) Generate a persistent (auto updating) list message."
        in_labs = pickle.load( open ("./persistence/labs.p", "rb" ) )
        self.labs = in_labs[0]
        self.mins = in_labs[1]
        self.pull_labs.start()
    
    @commands.Cog.listener()
    async def on_ready(self):
        #print( 'Logged on as {0}!'.format( self.user ) )
        #await self.change_presence(activity=discord.Game(name="Loading..."))
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
        labsString = self.getListStr() + "Quick Lab: " + self.getRLab()
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except Exception as err:
                print("Problem editting persistent message. {}".format(err), flush=True)
        #Grid message section
        labsString = self.getGridStr() + "Quick Lab: " + self.getRLab()
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=labsString, flush=True)
            except:
                print("Problem editting persistent message.", flush=True)
        labsString = self.getHybridStr() + "Quick Lab: " + self.getRLab()
        for msg in self.p_msg_hybrid:
            try:
                await msg.edit(content=labsString, flush=True)
            except:
                print("Problem editting persistent message.", flush=True)
    
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
                    users = self.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                labsString += "\n"
        return labsString + "\n```"
    
    def getHybridStr(self):
        labsString = "```nim\nLab Machine Users By Room  -:- Quick Labs\n"
        
        labs = sorted(self.labs,key=self.labs.get)
        ii = 0
        while ii < len(labs):
            if self.labs[labs[ii]] == -1:
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
                labsString += " -:- IP: " + self.getIP(labs[int(ii/2)]) + "\n  "
            ii = ii + 1
            for row in range(1,7):
                labsString += "  0" + str(row)
            if (ii % 2 == 0):
                labsString += " -:- " + labs[int(ii/2)] + "\n"
            else:
                labsString += " -:- IP: " + self.getIP(labs[int(ii/2)]) + "\n"
            ii = ii + 1
            for column in "abcd":
                labsString += "-" + str(column)
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    users = self.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                if (ii % 2 == 0):
                    labsString += " -:- " + labs[int(ii/2)] + "\n"
                else:
                    labsString += " -:- IP: " + self.getIP(labs[int(ii/2)]) + "\n"
                ii = ii + 1
        return labsString + "\n```"

    @tasks.loop(seconds=60)
    async def pull_labs(self):
        if self.loading:
            return
        print('Getting lab status')
        changed = False
        async with aiohttp.ClientSession() as session:
            async with session.get('http://35.189.5.47/machineList.txt') as resp:
                data = await resp.text()
                data = data.split("\n")[1:]
                mini = int(data[0].split(",")[3])
                mins = []
                for row in data:
                    parts = row.split(",")
                    if len(parts) < 4:
                        continue
                    host = f"lab{parts[0]}-{parts[1]}0{parts[2]}.cs.curtin.edu.au."
                    users = -1 if parts[3] == 'nil' else int(parts[3])
                    if self.labs[host] != users:
                        self.labs[host] = users
                        changed = True
                    if len(parts) > 4:
                        self.ips[host] = parts[4]
                    if (users>-1 and users < mini):
                        mini = users
                        mins = []
                    if (users == mini):
                        mins.append(host)
                self.mins = mins
                if changed:
                    max = -1
                    for lab in sorted(self.labs,key=self.labs.get):
                        if self.labs[lab] > max:
                            max = self.labs[lab]
                    if max != -1:
                        print("Saving up machines to file", flush=True)
                        pickle.dump( (self.labs,self.mins), open ("./persistence/labs.p", "wb" ) )
                    await self.bot.get_cog('Labs').updatePMsg()
                else:
                    print("No change since last pull")

    @pull_labs.before_loop
    async def before_pull_labs(self):
        print("Waiting for Bot to start before pulling labs.")
        await self.bot.wait_until_ready()

    def getRLab(self):
        return random.choice(self.mins)

    def getIP(self, hostname):
        if hostname in self.ips.keys():
            return ips[hostname]
        else:
            return "Unsupported"

def pad(inte,places):
    if inte < 1:
        padding = places-1
    else:
        padding = (places-int(1+math.log10(abs(inte))))
    return " " * padding



