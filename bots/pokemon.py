import os
import sys
from dotenv import load_dotenv
from discord.ext import commands

print('Loading dotenv')
load_dotenv()
try:
    POKEMON_BOT_TOKEN = os.getenv('DISCORD_POKEMON_BOT_TOKEN')
except:
    sys.exit('Failed to grab environment variable.')

print('Initializing bot.')
pokemon_bot = commands.Bot(command_prefix='!')
print('Loading cogs.pokemondb_cmds extension.')
pokemon_bot.load_extension('cogs.pokemondb_cmds')
print('Loading cogs.pokemon_tracking_cmds extension.')
pokemon_bot.load_extension('cogs.pokemon_tracking_cmds')
print('Starting bot.')
pokemon_bot.run(POKEMON_BOT_TOKEN)