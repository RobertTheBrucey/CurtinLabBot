import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import pickle

class BrayPull(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.pull_labs.start()

    @tasks.loop(seconds=60)
    async def pull_labs(self):
        while self.bot.get_cog('Labs').loading:
            await asyncio.sleep(5)
        print('Getting lab status')
        async with aiohttp.ClientSession() as session:
            async with session.get('http://35.189.5.47/machineList.txt') as resp:
                changed = False
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
                    if self.bot.get_cog('Labs').labs[host] != users:
                        self.bot.get_cog('Labs').labs[host] = users
                        changed = True
                    if len(parts) > 4:
                        try: 
                            if self.bot.get_cog('Labs').ips[host] != parts[4]:
                                self.bot.get_cog('Labs').ips[host] = parts[4]
                                changed = True
                        except:
                            self.bot.get_cog('Labs').ips[host] = parts[4]
                            changed = True
                    if (users>-1 and users < mini):
                        mini = users
                        mins = []
                    if (users == mini):
                        mins.append(host)
                self.bot.get_cog('Labs').mins = mins
                if changed:
                    max = -1
                    for lab in sorted(self.bot.get_cog('Labs').labs,key=self.bot.get_cog('Labs').labs.get):
                        if self.bot.get_cog('Labs').labs[lab] > max:
                            max = self.bot.get_cog('Labs').labs[lab]
                    if max != -1:
                        print("Saving up machines to file", flush=True)
                        pickle.dump( (self.bot.get_cog('Labs').labs,self.bot.get_cog('Labs').mins), open ("./persistence/labs.p", "wb" ) )
                    await self.bot.get_cog('Labs').updatePMsg()
                else:
                    print("No change since last pull")

    @pull_labs.before_loop
    async def before_pull_labs(self):
        print("Waiting for Bot to start before pulling labs.")
        await self.bot.wait_until_ready()