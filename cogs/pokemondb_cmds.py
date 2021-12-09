from discord.ext import commands

import scrapers.pokemondb as pokemondb

class PokemonDBCommands(commands.Cog):
    """ Contains commands used to access pokemondb. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'PokemonDBCommands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    async def __pokemon_lookup_cmd(self, ctx, lookup_fn, pokemon: str, *args, results_fm=lambda r: ', '.join(r)):
        # Validate args
        if len(args) > 0:
            await ctx.reply(f"Oh my, that's a lot of wild pokemon there. I can only lookup one at a time.")
            return

        # Get the field
        try:
            (success, results) = lookup_fn(pokemon)
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
            await ctx.reply(results_fm(results))
        else:
            await ctx.reply(f'Pokemon {pokemon} was not found in the Pokedex. Did you mean: {", ".join(results)}?')

    @commands.command("ev")
    async def ev_yield(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_ev_yield, pokemon, *args)

    @commands.command("types")
    async def types(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_types, pokemon, *args, results_fm=lambda r: ' and '.join(r))

    @commands.command("egg_groups")
    async def egg_groups(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_egg_groups, pokemon, *args)

    @commands.command("abilities")
    async def abilities(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_abilities, pokemon, *args, 
            results_fm=lambda r: '\n'.join([f'{r[i]}' if r[i].hidden else f'{i+1}. {r[i]}' for i in range(len(r))]))

def setup(bot):
    bot.add_cog(PokemonDBCommands(bot))
