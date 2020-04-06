import discord
import asyncio
import base64
import paramiko
import re
import datetime
import copy
import pickle
from multiprocessing import Process, Queue
from config import getCreds

#Todo: Persistent messages
#Grid view

reserved = ['simpintro','simp','unsimp','unsimpall']
class BotClient( discord.Client ):
    labs = {}
    p_msg = []
    p_msg_grid = []

    def __init__(self, ):
        super().__init__()
        self.helpString = ""
        try:
            self.labs = pickle.load( open( "/persistence/labs.p", "rb" ) )
            print("Labs successfully loaded.")
        except:
            print("No labs to load")
        asyncio.get_event_loop().create_task(self.pollLabs())

    async def on_ready( self ):
        print( 'Logged on as {0}!'.format( self.user ) )
        await self.change_presence(activity=discord.Game(name="^labhelp"))
        try:
            await self.loadPMsg()
            print("Persistent messages successfully loaded.")
        except:
            print("Couldn't load persistent messages from file.")
        await self.loadPMsg()

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
                labsString = "Available lab machines are:`"+labsString
                labsString = labsString[:labsString[:1999].rfind('\n')] + "`"
                await message.author.send(labsString)
                await message.channel.send("List of online lab machines DMed\nQuick machine: {}".format(first))
            elif command[1:] == "quicklab":
                print( '{} asked for a quick lab'.format(message.author))
                for lab in sorted(self.labs,key=self.labs.get):
                    await message.channel.send("Quick Lab: {}".format(lab))
                    break
            elif command[1:] == "labhelp":
                print( '{} asked for the lab help'.format(message.author))
                await message.channel.send("`^labs` - Request the list of Lab machines via DM\n`^quicklab` - Show a single ready lab machine\n`^labgrid` - Request a DM of Lab machine formatted in a grid.\n`^persistent` - (Administrator only) Generate a persistent (auto updating) message.")
            elif command[1:] == "persistent":
                print( '{} asked for a persistent message'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent message'.format(message.author))
                    labsString = ""
                    for lab in sorted(self.labs,key=self.labs.get):
                        if self.labs[lab] != -1:
                            labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
                    labsString = "Available lab machines are:`"+labsString
                    labsString = labsString[:labsString[:1999].rfind('\n')] + "`"
                    self.p_msg.append(await message.channel.send(labsString))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
            elif command[1:] == "labgrid":
                print( '{} asked for the lab machine grid'.format(message.author))
                await message.channel.send("Grid DMed to you")
                await message.author.send(self.getGridStr())
            elif command[1:] == "persistentgrid":
                print( '{} asked for a persistent lab machine grid'.format(message.author))
                if message.author.permissions_in(message.channel).manage_messages:
                    print( '{} was authorised for a persistent grid'.format(message.author))
                    self.p_msg_grid.append(await message.channel.send(self.getGridStr()))
                    await self.savePMsg()
                else:
                    await message.channel.send("You are not authorised to use this command.")
    def getGridStr(self):
        labsString = "Lab Machine Users By Room:\n"
        for room in [218,219,220,221,232]:
            labsString += "Room " + str(room) + ":\n\t"
            for row in range(1,7):
                labsString += str(row) + "\t"
            labsString += "\n"
            for column in "abcd":
                labsString += str(column) + "\t"
                for row in range(1,7):
                    host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                    labsString += str(("F",self.labs[host])[self.labs.get(host,-1)!=-1]) + "\t"
                labsString += "\n"
        return labsString

    async def pollLabs(self):
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
                        proc = Process(target=checkLab, args=(host,q))
                        #print("step 2")
                        proc.start()
                        #print("step 3")
                        try:
                            #print("Proc Join")
                            #proc.join(timeout=5)
                            #print("get queue")
                            users = q.get(timeout=3)
                            proc.join()
                            print(str(users) + " Users.")
                        except Exception as err:
                            proc.terminate()
                            print("Down")
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
                self.labs = pickle.load( open( "/persistence/labs.p", "rb" ) )
            else:
                print("Saving up machines to file")
                pickle.dump( self.labs, open ("/persistence/labs.p", "wb" ) )
            await self.updatePMsg()
            await asyncio.sleep(300)
            #a = False

    async def updatePMsg(self):
        labsString = ""
        for lab in sorted(self.labs,key=self.labs.get):
            if self.labs[lab] != -1:
                labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
        labsString = "Available lab machines are:`"+labsString
        labsString = labsString[:labsString[:1999].rfind('\n')] + "`"
        for msg in self.p_msg:
            try:
                await msg.edit(content=labsString)
            except:
                print("Problem editting persistent message.")
        #Grid message section
        labsString = self.getGridStr()
        for msg in self.p_msg_grid:
            try:
                await msg.edit(content=labsString)
            except:
                print("Problem editting persistent message.")

    async def loadPMsg(self):
        self.pmsg = []
        self.p_msg_grid = []
        msg_ids = pickle.load( open( "/persistence/pmsg.p", "rb" ) )
        for msg in msg_ids[0]:
            channels = self.get_all_channels()
            for channel in channels:
                try:
                    rmsg = await channel.get_message(msg)
                except:
                    continue
            if rmsg:
                self.p_msg.append(rmsg)
        for msg in msg_ids[1]:
            channels = self.get_all_channels()
            for channel in channels:
                try:
                    rmsg = await channel.get_message(msg)
                except:
                    continue
            if rmsg:
                self.p_msg_grid.append(rmsg)
        print("{} persistent messages loaded and {} persistent grids loaded" %(len(self.p_msg),len(self.p_msg_grid)))

    async def savePMsg(self):
        msg_ids = []
        grid_msg_ids = []
        for msg in self.p_msg:
            msg_ids.append(msg.id)
        for msg in self.p_msg_grid:
            grid_msg_ids.append(msg.id)
        msgs = (msg_ids,grid_msg_ids)
        pickle.dump( msgs, open ("/persistence/pmsg.p", "wb" ) )
    
def checkLab( host, temp ):
    sshclient = paramiko.SSHClient()
    creds = getCreds()
    sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
        sshclient.connect(host, username=creds[0], password=creds[1], timeout=2, banner_timeout=2, auth_timeout=2)
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