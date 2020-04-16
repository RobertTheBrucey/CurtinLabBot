import paramiko
from multiprocessing import Process, Queue
import datetime
import config
import pickle
import os.path
import math
import re
import discord
import botClient as bc
import asyncio
import time

class LabScan():
    def __init__(self, configfile):
        self.labs = {}
        self.mins = []
        self.configfile = configfile
        self.bot = None
        self.newLabs = False
        try:
            labt = pickle.load( open( "./persistence/labs.p", "rb" ) )
            self.labs = labt[0]
            self.mins = labt[1]
            print("Labs successfully loaded.")
        except:
            print("No labs to load")

    def pollLabs(self):
        sp = 2
        creds = config.getCreds(self.configfile)
        logfile = "./persistence/"+config.getLogfile(self.configfile)
        keyfile = "./persistence/"+config.getKeyfile(self.configfile)
        while True:
            print("Starting scan at {}".format(str(datetime.datetime.now())), flush=True)
            mini = 100
            mins = []
            for room in [218,219,220,221,232]:
                print("lab" + str(room) + ":\n  ", end='', flush=True)
                for row in range(1,7):
                    print( "  0" + str(row), end='', flush=True)
                print("")
                for column in "abcd":
                    print("-" + str(column), end='', flush=True)
                    for row in range(1,7):
                        try:
                            users = -1
                            host = "lab{}-{}0{}.cs.curtin.edu.au.".format(room,column,row)
                            q = Queue()
                            proc = Process(target=checkLab, args=(host,q,creds,keyfile))
                            proc.start()
                            try:
                                users = q.get(timeout=2)
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
                            print("  " + str((" ",users)[users!=-1]) + pad(users,sp), end = '', flush=True)
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
                pickle.dump( (self.labs,self.mins), open ("./persistence/labs.p", "wb" ) )
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
            if self.bot:
                self.bot.updatePMsg()
            self.newLabs = True
            #asyncio.create_task(self.bot.updatePMsg())
            time.sleep(300)

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