from discord.ext import commands

class WritingGreetings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'WritingGreetings connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Hi {member.name}! I hereby welcome you to the Writing Discord!'
        )

def setup(bot):
    bot.add_cog(WritingGreetings(bot))
