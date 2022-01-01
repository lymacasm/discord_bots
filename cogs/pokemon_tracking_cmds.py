import os
import discord
from discord.ext import commands

import tracking.pokemon as poketrack
import tracking.pokemon.factory as poketrack_factory
import utility.pokemon as poke_classes
import scrapers

class PokemonTrackingCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Create the tracking class, pulling from enviroment variable to determine the type
        try:
            POKEMON_TRACKING_TYPE = os.getenv('POKEMON_TRACKING_TYPE')
        except:
            print('Failed to find environment variable POKEMON_TRACKING_TYPE. Using FILES as defualt.')
            POKEMON_TRACKING_TYPE = poketrack_factory.TrackingTypes.FILES
        self.pokemon_tracking = poketrack_factory.tracking_factory(POKEMON_TRACKING_TYPE)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'PokemonTrackingCommmands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    def get_user(self, ctx):
        return str(ctx.message.author.id)

    @commands.command("track-add")
    async def setup_tracking(self, ctx, pokemon: str, nature: str, nickname = '', *args):
        try:
            await ctx.reply(self.pokemon_tracking.add_pokemon(self.get_user(ctx), pokemon, nature, nickname))
        except scrapers.SuggestionException as suggestions:
            await ctx.reply(f'Pokemon {pokemon} was not found in the Pokedex. Did you mean: {suggestions}?')

    @commands.command("track-list")
    async def get_pokemon_list(self, ctx, *args):
        await ctx.reply(self.pokemon_tracking.get_all_pokemon(self.get_user(ctx)))

    @commands.command("track-get-base")
    async def get_pokemon_base_stats(self, ctx, pokemon_id: int, *args):
        await ctx.reply(self.pokemon_tracking.get_base_stats(self.get_user(ctx), pokemon_id))

    @commands.command("track-get-evs")
    async def get_pokemon_evs(self, ctx, pokemon_id: int, *args):
        await ctx.reply(self.pokemon_tracking.get_evs(self.get_user(ctx), pokemon_id))

    @commands.command("track-get-ivs")
    async def get_pokemon_ivs(self, ctx, pokemon_id: int, *args):
        await ctx.reply(poke_classes.get_stat_range_str(*self.pokemon_tracking.get_ivs(self.get_user(ctx), pokemon_id)))

    @commands.command("track-set-ivs")
    async def set_pokemon_ivs(self, ctx, pokemon_id: int, hp: str, attack: str, defense: str, sp_atk: str, sp_def: str, speed: str, *args):
        await ctx.reply(poke_classes.get_stat_range_str(*self.pokemon_tracking.set_ivs(self.get_user(ctx), pokemon_id, hp, attack, defense, sp_atk, sp_def, speed)))

    @commands.command("track-get-stats")
    async def get_pokemon_stats(self, ctx, pokemon_id: int, level: int, *args):
        await ctx.reply(poke_classes.get_stat_range_str(*self.pokemon_tracking.get_pokemon_stats(self.get_user(ctx), pokemon_id, level)))

    @commands.command("track-set-evolution")
    async def set_pokemon_evolution(self, ctx, pokemon_id: int, evolution_name: str, *args):
        await ctx.reply(self.pokemon_tracking.change_evolution(self.get_user(ctx), pokemon_id, evolution_name))

def setup(bot):
    bot.add_cog(PokemonTrackingCommands(bot))
