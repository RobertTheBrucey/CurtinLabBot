from aiohttp import web
from discord.ext import commands, tasks
import discord
import os
import aiohttp

app = web.Application()
routes = web.RouteTableDef()

class Webserver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server.start()

        @routes.get('/lab')
        async def send_lab(request):
            return web.Response(text=self.bot.get_cog('Labs').getRLab())

        @routes.get('/labip')
        async def send_lab_ip(request):
            return web.Response(text=self.bot.get_cog('Labs').getRLabIP())

        @routes.get('/laball')
        async def send_lab_all(request):
            csv = "hostname,cpu1min,cpu5min,cpu15min,users,ip\n"
            for lab in self.bot.get_cog('Labs').labs:
                print(type(lab))
                csv += f"{lab.host},{lab.load1min},{lab.load5min},{lab.load15min},{lab.users},{lab.ip}\n"
            return web.Response(text=csv)

        self.webserver_port = os.environ.get('PORT', 8010)
        app.add_routes(routes)


    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()