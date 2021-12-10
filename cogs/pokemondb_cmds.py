import discord
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
            print(f'WebRequestException in get_ev_yield call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} whited out! Turns out {pokemon} isn't a real pokemon.")
            return
        except pokemondb.WebParseException as e:
            print(f'WebParseException in get_synonym call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} used SPLASH! It had no effect. Please contact tech support to fix your broken pokemon.")
            return

        # Return result
        if success:
            await ctx.reply(results_fm(results))
        else:
            await ctx.reply(f'Pokemon {pokemon} was not found in the Pokedex. Did you mean: {", ".join(results)}?')

    async def __egg_group_lookup_cmd(self, ctx, lookup_fn, egg_group: str, *args, join_str=', '):
        # Validate args
        if len(args) > 0:
            egg_group = '-'.join([egg_group] + list(args))

        # Get the field
        try:
            (success, results) = lookup_fn(egg_group)
        except pokemondb.WebRequestException as e:
            print(f'WebRequestException in get_ev_yield call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} whited out! Pokemon daycare is exhausting, so I decided not to grab egg group of {egg_group} for you.")
            return
        except pokemondb.WebParseException as e:
            print(f'WebParseException in get_synonym call: {e}\n')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} used SPLASH! It had no effect. Please contact tech support to fix your broken pokemon.")
            return

        # Return result
        if success:
            result_str = ''
            for i in range(len(results)):
                if i == 0:
                    result_str = str(results[i])
                elif (len(result_str) + len(str(results[i])) + len(join_str)) > 2000:
                    await ctx.reply(result_str)
                    result_str = str(results[i])
                else:
                    result_str += ', ' + str(results[i])
            await ctx.reply(result_str)
        else:
            await ctx.reply(f"Egg group {egg_group} doesn't exist. Did you mean: {', '.join(results)}?")

    @commands.command("ev")
    async def ev_yield(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_ev_yield, pokemon, *args)

    @commands.command("types")
    async def types(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_types, pokemon, *args, results_fm=lambda r: ' and '.join(r))

    @commands.command("evolutions")
    async def evolutions(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_evolutions, pokemon, *args, results_fm=lambda r: '\n'.join(r))

    @commands.command("egg_groups")
    async def egg_groups(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_egg_groups, pokemon, *args)

    @commands.command("egg_group")
    async def egg_group(self, ctx, egg_group: str, *args):
        await self.__egg_group_lookup_cmd(ctx, pokemondb.get_egg_group_pokemon, egg_group, *args)

    @commands.command("abilities")
    async def abilities(self, ctx, pokemon: str, *args):
        await self.__pokemon_lookup_cmd(ctx, pokemondb.get_abilities, pokemon, *args, 
            results_fm=lambda r: '\n'.join([f'{r[i]}' if r[i].hidden else f'{i+1}. {r[i]}' for i in range(len(r))]))

    @commands.command("view")
    async def view_pokemon(self, ctx, pokemon: str, *args):
        if len(args) > 0:
            await ctx.reply(f"Oh my, that's a lot of wild pokemon there. I can only lookup one at a time.")
            return

        try:
            url = pokemondb.get_pokemon_image_url(pokemon)
        except pokemondb.WebRequestException as e:
            print(f'WebRequestException in get_pokemon_image: {e}')
            await ctx.reply(f"{str(self.bot.user).split('#')[0]} whited out! Turns out {pokemon} isn't a real pokemon.")
            return

        embed = discord.Embed(color=0xffffff)
        embed.set_image(url=url)
        await ctx.reply(embed=embed)

def setup(bot):
    bot.add_cog(PokemonDBCommands(bot))
