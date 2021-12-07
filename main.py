import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
WRITING_BOT_TOKEN = os.getenv('DISCORD_WRITING_BOT_TOKEN')

writing_bot = commands.Bot(command_prefix='!')
writing_bot.load_extension('cogs.writing_greetings')
writing_bot.load_extension('cogs.thesaurus_cmds')
writing_bot.run(WRITING_BOT_TOKEN)