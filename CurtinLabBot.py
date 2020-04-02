import discord
import botClient as bc
from config import getToken

""" Setup """
client = bc.BotClient()
client.run(getToken())
