from discord.ext import commands

import utility.poetry as poetry

class PoetryListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'PoetryListener connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.Cog.listener("on_message")
    async def check_for_haiku(self, message):
        if message.author == self.bot.user:
            return

        # Check for a haiku 
        try:
            poetry_lines = poetry.matches_syllables_scheme(message.content, [5, 7, 5])
            poetry_msg = '>>> {}\n\n*Haiku by {}*'.format('\n'.join(poetry_lines), str(message.author).split('#')[0])
            await message.channel.send(poetry_msg)
        except poetry.SyllableSchemeMismatchError as e:
            pass

def setup(bot):
    bot.add_cog(PoetryListener(bot))
