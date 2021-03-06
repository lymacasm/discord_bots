import os
import discord
from discord.ext import commands

import tracking.pokemon as poketrack
import tracking.pokemon.factory as poketrack_factory
import scrapers

class PokemonTrackingCommands(commands.Cog):
    undo_count = 10 # default value

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Create the tracking class, pulling from enviroment variable to determine the type
        try:
            POKEMON_TRACKING_TYPE = os.environ['POKEMON_TRACKING_TYPE']
            print(f'Using tracking type of {POKEMON_TRACKING_TYPE}.')
        except:
            print('Failed to find environment variable POKEMON_TRACKING_TYPE. Using FILES as default.')
            POKEMON_TRACKING_TYPE = poketrack_factory.TrackingTypes.FILES
        self.pokemon_tracking = poketrack_factory.tracking_factory(POKEMON_TRACKING_TYPE)

        # Create an undo list for the undo command
        try:
            self.undo_count = int(os.environ['POKEMON_TRACKING_UNDO_COUNT'])
            print(f'Using undo count of {self.undo_count}.')
        except:
            self.undo_count = PokemonTrackingCommands.undo_count
            print(f'Failed to find environment varialbe POKEMON_TRACKING_UNDO_COUNT. Using {self.undo_count} as default.')
        self.undo_list = {} # type: dict[str, list[tuple]]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'PokemonTrackingCommmands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    def get_user(self, ctx):
        return str(ctx.message.author.id)

    def add_to_undo_list(self, user, tracking_fn, *args):
        if user not in self.undo_list:
            self.undo_list[user] = []
        
        self.undo_list[user].append((tracking_fn, args))
        if len(self.undo_list[user]) > self.undo_count:
            self.undo_list[user].pop(0) # Remove from beginning of list (oldest command)

    async def __pokemon_lookup_tracking_cmd(self, ctx, tracking_fn, pokemon, *args, publish_on_success=True) -> bool:
        user = self.get_user(ctx)
        try:
            result = tracking_fn(user, pokemon, *args)
            if publish_on_success:
                await ctx.reply(result)
            return (True, result)
        except scrapers.SuggestionException as suggestions:
            await ctx.reply(f'Pokemon {pokemon} was not found in the Pokedex. Did you mean: {suggestions}?')
            return (False, None)
        except poketrack.PokemonTrackingException as e:
            await ctx.reply(e)
            return (False, None)

    async def __generic_tracking_cmd(self, ctx, tracking_fn, *args) -> bool:
        user = self.get_user(ctx)
        try:
            await ctx.reply(tracking_fn(user, *args))
            return True
        except (scrapers.SuggestionException, poketrack.PokemonTrackingException) as e:
            await ctx.reply(e)
            return False

    @commands.command("track-add")
    async def setup_tracking(self, ctx, pokemon: str, nature: str, nickname = '', *args):
        success, pokemon_id = await self.__pokemon_lookup_tracking_cmd(ctx, self.pokemon_tracking.add_pokemon, pokemon, nature, nickname, publish_on_success=False)
        if success:
            self.add_to_undo_list(self.get_user(ctx), self.__generic_tracking_cmd, ctx, self.pokemon_tracking.remove_pokemon_str, pokemon_id)
            await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_full_name_str, pokemon_id)

    @commands.command("track-remove")
    async def remove_tracking(self, ctx, pokemon_id: int):
        # Try and remove the pokemon
        user = self.get_user(ctx)
        try:
            pokemon = self.pokemon_tracking.remove_pokemon(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            await ctx.reply(e)
            return

        # Add pokemon to undo list
        self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.add_pokemon_obj_str, pokemon, pokemon_id)

        # Get the new list
        response = f'Removed pokemon: **{pokemon.get_name()}**\n\n'
        try:
            response += f'New list:\n{self.pokemon_tracking.get_all_pokemon(user)}'
        except poketrack.PokemonTrackingException as e:
            response += str(e)
        await ctx.reply(response)

    @commands.command("track-list")
    async def get_pokemon_list(self, ctx):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_all_pokemon)

    @commands.command("track-list-evs")
    async def get_all_pokemon_evs(self, ctx):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_evs_all_str)

    @commands.command("track-set-nickname")
    async def set_pokemon_nickname(self, ctx, pokemon_id: int, nickname: str):
        user = self.get_user(ctx)
        try:
            old_nickname = self.pokemon_tracking.get_nickname(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old nickname. Error: {e}')
            old_nickname = nickname

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.set_nickname_str, pokemon_id, nickname):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_nickname_str, pokemon_id, old_nickname)

    @commands.command("track-get-base")
    async def get_pokemon_base_stats(self, ctx, pokemon_id: int):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_base_stats_str, pokemon_id)

    @commands.command("track-get-evs")
    async def get_pokemon_evs(self, ctx, pokemon_id: int):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_evs_str, pokemon_id)

    @commands.command("track-set-evs")
    async def set_pokemon_evs(self, ctx, pokemon_id: int, hp: int, attack: int, defense: int, sp_atk: int, sp_def: int, speed: int):
        user = self.get_user(ctx)
        try:
            old_evs = self.pokemon_tracking.get_evs(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old EVs. Error: {e}')
            old_evs = poketrack.PokemonStats(hp, attack, defense, sp_atk, sp_def, speed)

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.set_evs_str, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs, pokemon_id, old_evs.hp, old_evs.attack, old_evs.defense, old_evs.sp_atk,
                old_evs.sp_def, old_evs.speed)

    @commands.command("track-get-goal-evs")
    async def get_pokemon_goal_evs(self, ctx, pokemon_id: int):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_goal_evs_str, pokemon_id)

    @commands.command("track-set-goal-evs")
    async def set_pokemon_goal_evs(self, ctx, pokemon_id: int, hp: int, attack: int, defense: int, sp_atk: int, sp_def: int, speed: int):
        user = self.get_user(ctx)
        try:
            old_goal_evs = self.pokemon_tracking.get_goal_evs(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old EVs. Error: {e}')
            old_goal_evs = None

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.set_goal_evs_str, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed):
            if old_goal_evs is None:
                self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.remove_goal_evs_str, pokemon_id)
            else:
                self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs, pokemon_id, old_goal_evs.hp, old_goal_evs.attack, old_goal_evs.defense, old_goal_evs.sp_atk,
                    old_goal_evs.sp_def, old_goal_evs.speed)

    @commands.command("track-rem-goal-evs")
    async def rem_pokemon_goal_evs(self, ctx, pokemon_id: int):
        user = self.get_user(ctx)
        try:
            old_goal_evs = self.pokemon_tracking.get_goal_evs(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old EVs. Error: {e}')
            old_goal_evs = None

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.remove_goal_evs_str, pokemon_id):
            if old_goal_evs is None:
                self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.remove_goal_evs_str, pokemon_id)
            else:
                self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs, pokemon_id, old_goal_evs.hp, old_goal_evs.attack, old_goal_evs.defense, old_goal_evs.sp_atk,
                    old_goal_evs.sp_def, old_goal_evs.speed)

    @commands.command("track-get-ivs")
    async def get_pokemon_ivs(self, ctx, pokemon_id: int):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_ivs_str, pokemon_id)

    @commands.command("track-set-ivs")
    async def set_pokemon_ivs(self, ctx, pokemon_id: int, hp: str, attack: str, defense: str, sp_atk: str, sp_def: str, speed: str, *args):
        user = self.get_user(ctx)
        try:
            old_ivs_min, old_ivs_max = self.pokemon_tracking.get_ivs(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print('Failed to get old IVs.')
            old_ivs_min = poketrack.PokemonStats(max_val=31)
            old_ivs_max = poketrack.PokemonStats(31, 31, 31, 31, 31, 31, max_val=31)

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.set_ivs_str, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_ivs_exact_str, pokemon_id, old_ivs_min, old_ivs_max)

    @commands.command("track-get-stats")
    async def get_pokemon_stats(self, ctx, pokemon_id: int, level: int):
        await ctx.reply(self.pokemon_tracking.get_pokemon_stats_str(self.get_user(ctx), pokemon_id, level))

    @commands.command("track-set-evolution")
    async def set_pokemon_evolution(self, ctx, pokemon_id: int, evolution_name: str, *args):
        user = self.get_user(ctx)
        try:
            old_name = self.pokemon_tracking.get_pokemon_name(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print('Failed to get pokemon name.')
            old_name = evolution_name

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.change_evolution, pokemon_id, evolution_name):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.change_evolution, pokemon_id, old_name)

    @commands.command("track-set-form")
    async def set_pokemon_form(self, ctx, pokemon_id: int, form_name: str, *args):
        user = self.get_user(ctx)
        try:
            old_name = self.pokemon_tracking.get_form_name(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print('Failed to get form name.')
            old_name = form_name

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.change_form, pokemon_id, form_name):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.change_form, pokemon_id, old_name)

    @commands.command("track-add-defeat")
    async def add_defeated_pokemon(self, ctx, defeated_pokemon: str, *pokemon_ids_received_exp):
        pokemon_ids = []
        try:
            for id in pokemon_ids_received_exp:
                pokemon_ids.append(int(id))
        except ValueError as e:
            print(f'Failed to convert id of {id} to an integer. Error: {e}')
            return

        # Get the old EV's for the undo command
        old_evs = []
        ids = []
        user = self.get_user(ctx)
        for pokemon_id in pokemon_ids:
            try:
                evs = self.pokemon_tracking.get_evs(user, pokemon_id)
                old_evs.append(evs)
                ids.append(pokemon_id)
            except poketrack.PokemonTrackingException as e:
                print(f'Failed to get old EV. Error: {e}')

        if await self.__pokemon_lookup_tracking_cmd(ctx, self.pokemon_tracking.add_defeated_pokemon_str, defeated_pokemon, pokemon_ids):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs_multiple_pokemon_str, ids, old_evs)

    @commands.command("track-add-vitamin")
    async def add_vitamin(self, ctx, pokemon_id: int, vitamin: str, count=1):
        user = self.get_user(ctx)
        try:
            evs = [self.pokemon_tracking.get_evs(user, pokemon_id)]
            ids = [pokemon_id]
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old EV. Error: {e}')
            evs = []
            ids = []

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.consume_ev_vitamin_str, pokemon_id, vitamin, count):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs_multiple_pokemon_str, ids, evs)

    @commands.command("track-add-berry")
    async def add_berry(self, ctx, pokemon_id: int, berry: str, count=1):
        user = self.get_user(ctx)
        try:
            evs = [self.pokemon_tracking.get_evs(user, pokemon_id)]
            ids = [pokemon_id]
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get old EV. Error: {e}')
            evs = []
            ids = []

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.consume_ev_berry_str, pokemon_id, berry, count):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_evs_multiple_pokemon_str, ids, evs)

    @commands.command("track-get-nature")
    async def get_nature(self, ctx, pokemon_id: int):
        await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.get_nature_str, pokemon_id)

    @commands.command("track-set-nature")
    async def set_nature(self, ctx, pokemon_id: int, nature: str):
        user = self.get_user(ctx)
        try:
            old_nature = self.pokemon_tracking.get_nature(user, pokemon_id)
        except poketrack.PokemonTrackingException as e:
            print(f'Failed to get nature. Error: {e}')
            old_nature = nature

        if await self.__generic_tracking_cmd(ctx, self.pokemon_tracking.set_nature_str, pokemon_id, nature):
            self.add_to_undo_list(user, self.__generic_tracking_cmd, ctx, self.pokemon_tracking.set_nature_str, pokemon_id, old_nature)

    @commands.command("track-undo")
    async def undo(self, ctx):
        user = self.get_user(ctx)
        if user in self.undo_list:
            undo_tuple = self.undo_list[user].pop(-1)
            if len(self.undo_list[user]) == 0:
                del self.undo_list[user]
            await undo_tuple[0](*undo_tuple[1])
        else:
            await ctx.reply('No commands to undo.')

def setup(bot):
    bot.add_cog(PokemonTrackingCommands(bot))
