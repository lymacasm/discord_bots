from discord.ext import commands

import scrapers.pokemondb as pokemondb

class PokemonDBCommands(commands.Cog):
    """ Contains commands used to access pokemondb. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'PokemonDBCommands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.command("ev")
    async def ev_yield(self, ctx, pokemon: str, *args):
        # Validate args
        if len(args) > 0:
            await ctx.reply(f"Oh my, that's a lot of wild pokemon there. I can only lookup one at a time.")
            return

        # Get EV Yield
        try:
            (success, result) = pokemondb.get_ev_yield(pokemon)
        except pokemondb.WebRequestException as e:
            with open('err.log', 'a') as f:
                f.write(f'WebRequestException in get_ev_yield call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} whited out! Turns out {pokemon} isn't a real pokemon.")
            return
        except pokemondb.WebParseException as e:
            with open('err.log', 'a') as f:
                f.write(f'WebParseException in get_synonym call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} used SPLASH! It had no effect. Please contact tech support to fix your broken pokemon.")
            return

        # Return result
        if success:
            await ctx.reply(result)
        else:
            await ctx.reply(f'Pokemon {pokemon} was not found in the Pokedex. Did you mean: {", ".join(result)}?')

def setup(bot):
    bot.add_cog(PokemonDBCommands(bot))
