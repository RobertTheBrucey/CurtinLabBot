import discord
import time
import asyncio
import base64
import paramiko
import socket
import re
import signal
import datetime
from contextlib import contextmanager
from multiprocessing import Process, Queue
from config import getCreds

reserved = ['simpintro','simp','unsimp','unsimpall']
class BotClient( discord.Client ):
    labs = {}

    def __init__(self, ):
        super().__init__()
        self.helpString = ""

    async def on_ready( self ):
        print( 'Logged on as {0}!'.format( self.user ) )
        asyncio.get_event_loop().create_task(self.pollLabs())
        #self.activity("^labhelp")

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
                print( '\n{} asked for the lab machines'.format(message.author))
                labsString = ""
                first = ""
                for lab in sorted(self.labs,key=self.labs.get):
                    if first == "":
                        first = lab
                    if self.labs[lab] != -1:
                        #labsString += "\n{} has {} user{}".format((lab,str(self.labs[lab])),("","s")[self.labs[lab]==1])
                        labsString += "\n"+lab+" has "+str(self.labs[lab])+" user(s)"
                labsString = "Available lab machines are:`"+labsString
                labsString = labsString[:labsString[:1999].rfind('\n')] + "`"
                await message.author.send(labsString)
                await message.channel.send("List of online lab machines DMed\nQuick machine: {}".format(first))
            elif command[1:] == "quicklab":
                print( '\n{} asked for a quick lab'.format(message.author))
                for lab in sorted(self.labs,key=self.labs.get):
                    await message.channel.send("Quick Lab: {}".format(lab))
                    break
            elif command[1:] == "labhelp":
                await message.channel.send("Type ^labs for a list of Lab machines to be DMed to you\nType ^quicklab for a single free lab machine")

    async def pollLabs(self):
        while True:
            print("Starting scan at {}\n".format(str(datetime.datetime.now())))
            for room in [218,219,220,221,232]:
                for column in "abcd":
                    for row in range(1,7):
                        users = -1
                        host = "\033[1Alab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                        print(host)
                        q = Queue()
                        #print("step 1")
                        proc = Process(target=self.checkLab, args=(host,q))
                        #print("step 2")
                        proc.start()
                        #print("step 3")
                        try:
                            proc.join(timeout=5)
                            users = q.get_nowait()
                        except:
                            proc.terminate()
                        #print("step 4")
                        self.labs[host] = users
                        #print("End of thingy")
                        await asyncio.sleep(1)
            print("Finishing scan at {}".format(str(datetime.datetime.now())))
            await asyncio.sleep(300)
            #a = False
    
    def checkLab( self, host, temp ):
        sshclient = paramiko.SSHClient()
        creds = getCreds()
        sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        try:
            sshclient.connect(host, username=creds[0], password=creds[1], timeout=2, banner_timeout=2, auth_timeout=2)
            stdin, stdout, stderr = sshclient.exec_command('w',timeout=2)
            for line in stderr:
                print(line.strip('\n'))
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

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError
