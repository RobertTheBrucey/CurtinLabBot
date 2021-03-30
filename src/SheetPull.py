import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from Lab import Lab

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = './persistence/credentials.json'

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1OP8rMUbdNE1UprSoYGNZxRSEC3gUDFDOcmtcJD5HXR4'
SAMPLE_RANGE_NAME = 'Load Average!C2:H'

class SheetPull(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.pull_labs.start()

    @tasks.loop(seconds=60)
    async def pull_labs(self):
        while self.bot.get_cog('Labs').loading:
            await asyncio.sleep(5)
        print('Getting lab status')
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        data = result.get('values', [])
        changed = False
        mini = int(data[1][4])
        mins = []
        max = -1
        for row in data:
            host = f"{row[0]}.cs.curtin.edu.au."
            lab = self.bot.get_cog('Labs').labs[host] if host in self.bot.get_cog('Labs').labs.keys() else Lab(host)
            self.bot.get_cog('Labs').labs[host] = lab
            users = -1 if row[4] == 'N/A' else int(row[4])
            max = max if users <= max else users
            if lab.users != users:
                lab.users = users
                changed = True
            if len(row) > 5:
                if lab.ip != row[5]:
                    lab.ip = row[5]
                    changed = True
            if lab.load1min != load_to_float(row[1]):
                lab.load1min = load_to_float(row[1])
                changed = True
            if lab.load5min != load_to_float(row[2]):
                lab.load5min = load_to_float(row[2])
                changed = True
            if lab.load15min != load_to_float(row[3]):
                lab.load15min = load_to_float(row[3])
                changed = True
            if (users>-1 and users < mini):
                mini = users
                mins = []
            if (users == mini):
                mins.append(lab)
        self.bot.get_cog('Labs').mins = mins
        if changed:
            if max != -1:
                print("Saving up machines to file", flush=True)
                pickle.dump( (self.bot.get_cog('Labs').labs,self.bot.get_cog('Labs').mins), open ("./persistence/labsn.p", "wb" ) )
            await self.bot.get_cog('Labs').updatePMsg()
            print("Persistent Messages Updated")
        else:
            print("No change since last pull")

    @pull_labs.before_loop
    async def before_pull_labs(self):
        print("Waiting for Bot to start before pulling labs.")
        await self.bot.wait_until_ready()

def load_to_float(load):
    return -1.0 if load == "N/A" else float(load)