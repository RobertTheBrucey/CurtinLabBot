import discord
from discord.ext import commands, tasks
import pickle
import math

listLen = 1000

class Labs(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.owner = None
        self.loading = True
        self.p_msg = []
        self.p_msg_grid = []
        self.p_msg_hybrid = []
    
    @commands.Cog.listener()
    async def on_ready(self):
        print( 'Logged on as {0}!'.format( self.user ) )
        await self.change_presence(activity=discord.Game(name="Loading..."))
        try:
            await self.loadPMsg()
            print("Persistent messages successfully loaded.")
        except:
            print("Couldn't load persistent messages from file.")
        self.loading = False
        await self.change_presence(activity=discord.Game(name="^labhelp"))
        appinfo = await self.application_info()
        self.owner = appinfo.owner

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
                    users = self.labs.get(host,-1)
                    labsString +=  "  " + str((" ",users)[users!=-1]) + pad(users,sp)
                if (ii % 2 == 0):
                    labsString += " -:- " + labs[int(ii/2)] + "\n"
                else:
                    labsString += " -:- IP: " + getIP(labs[int(ii/2)]) + "\n"
                ii = ii + 1
        return labsString + "\n```"

    @tasks.loop(seconds=60)
    async def pull_labs(self):
        print('Getting lab status')
        async with aiohttp.ClientSession() as session:
            async with session.get('http://35.189.5.47/machineList.txt') as resp:
                data = await resp.text()
                data = data.split("\n")[1:]
                mini = data[0].split(",")[3]
                for row in data:
                    parts = row.split(",")
                    host = f"lab{parts[0]}-{parts[1]}0{parts[2]}.cs.curtin.edu.au."
                    users = -1 if parts[3] == 'nil' else int(parts[3])
                    self.labs[host] = users
                    if (users>-1 and users < mini):
                        mini = users
                        mins = []
                    if (users == mini):
                        mins.append(host)
                self.mins = mins
                max = -1
                for lab in sorted(self.labs,key=self.labs.get):
                    if self.labs[lab] > max:
                        max = self.labs[lab]
                if max != -1:
                    print("Saving up machines to file", flush=True)
                    pickle.dump( (self.labs,self.mins), open ("./persistence/labs.p", "wb" ) )
                await updatePMsg(self.labs)

    @pull_labs.before_loop
    async def before_pull_labs(self):
        print("Waiting for Bot to start before pulling labs.")
        await self.wait_until_ready()

def pad(inte,places):
    if inte < 1:
        padding = places-1
    else:
        padding = (places-int(1+math.log10(abs(inte))))
    return " " * padding

def getIP(hostname):
    return "Not Currently Supported"