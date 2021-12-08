import os
import sys
from dotenv import load_dotenv
from discord.ext import commands

print('Loading dotenv')
load_dotenv()
try:
    WRITING_BOT_TOKEN = os.getenv('DISCORD_WRITING_BOT_TOKEN')
except:
    sys.exit('Failed to grab environment variable.')

print('Getting bot setup.')
writing_bot = commands.Bot(command_prefix='!')
print('Loading extension 1')
writing_bot.load_extension('cogs.writing_greetings')
print('Loading extension 2')
writing_bot.load_extension('cogs.thesaurus_cmds')
print('Starting bot.')
writing_bot.run(WRITING_BOT_TOKEN)