from utility.pokemon import PokemonStats, PokemonStatsError, compute_stats, get_stat_range_str
import scrapers
import scrapers.pokemondb as pokemondb

class PokemonTrackingException(Exception):
    pass

class PokemonNotFoundException(PokemonTrackingException):
    pass

class UserNotFoundException(PokemonTrackingException):
    pass

_iv_name_map = {
    'nogood': (0, 0),
    'decent': (1, 10),
    'prettygood': (11, 20),
    'verygood': (21, 29),
    'fantastic': (30, 30),
    'best': (31, 31)
}

_natures_map = {
    'lonely': PokemonStats(1.0, 1.1, 0.9, 1.0, 1.0, 1.0),
    'brave': PokemonStats(1.0, 1.1, 1.0, 1.0, 1.0, 0.9),
    'adamant': PokemonStats(1.0, 1.1, 1.0, 0.9, 1.0, 1.0),
    'naughty': PokemonStats(1.0, 1.1, 1.0, 1.0, 0.9, 1.0),
    'bold': PokemonStats(1.0, 0.9, 1.1, 1.0, 1.0, 1.0),
    'relaxed': PokemonStats(1.0, 1.0, 1.1, 1.0, 1.0, 0.9),
    'impish': PokemonStats(1.0, 1.0, 1.1, 0.9, 1.0, 1.0),
    'lax': PokemonStats(1.0, 1.0, 1.1, 1.0, 0.9, 1.0),
    'timid': PokemonStats(1.0, 0.9, 1.0, 1.0, 1.0, 1.1),
    'hasty': PokemonStats(1.0, 1.0, 0.9, 1.0, 1.0, 1.1),
    'jolly': PokemonStats(1.0, 1.0, 1.0, 0.9, 1.0, 1.1),
    'naive': PokemonStats(1.0, 1.0, 1.0, 1.0, 0.9, 1.1),
    'modest': PokemonStats(1.0, 0.9, 1.0, 1.1, 1.0, 1.0),
    'mild': PokemonStats(1.0, 1.0, 0.9, 1.1, 1.0, 1.0),
    'quiet': PokemonStats(1.0, 1.0, 1.0, 1.1, 1.0, 0.9),
    'rash': PokemonStats(1.0, 1.0, 1.0, 1.1, 0.9, 1.0),
    'calm': PokemonStats(1.0, 0.9, 1.0, 1.0, 1.1, 1.0),
    'gentle': PokemonStats(1.0, 1.0, 0.9, 1.0, 1.1, 1.0),
    'sassy': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.1, 0.9),
    'careful': PokemonStats(1.0, 1.0, 1.0, 0.9, 1.1, 1.0),
    'hardy': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    'docile': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    'serious': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    'bashful': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    'quirky': PokemonStats(1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
}

_vitamins_map = {
    'hpup': PokemonStats(hp=10),
    'protein': PokemonStats(attack=10),
    'iron': PokemonStats(defense=10),
    'calcium': PokemonStats(sp_attack=10),
    'zinc': PokemonStats(sp_defense=10),
    'carbos': PokemonStats(speed=10),
}

_berries_map = {
    'pomeg': PokemonStats(hp=-10, min_val=-10),
    'kelpsy': PokemonStats(attack=-10, min_val=-10),
    'qualot': PokemonStats(defense=-10, min_val=-10),
    'hondew': PokemonStats(sp_attack=-10, min_val=-10),
    'grepa': PokemonStats(sp_defense=-10, min_val=-10),
    'tamato': PokemonStats(speed=-10, min_val=-10),
}

class Pokemon:
    def __init__(self, pokemon_name: str, nature: str, nickname = ''):
        self._name = pokemon_name.capitalize()
        self._nature_name = nature.capitalize()
        self.nickname = nickname
        self.evs = PokemonStats(max_val=252, max_total=510)
        self.ivs_min = PokemonStats(0, 0, 0, 0, 0, 0)
        self.ivs_max = PokemonStats(31, 31, 31, 31, 31, 31)
        self.nature = _natures_map[self._nature_name.lower()]
        try:
            self.base_stats = pokemondb.get_base_stats(self._name)
        except scrapers.SuggestionException as suggestions:
            raise PokemonNotFoundException(f'Pokemon {self._name} was not found in the Pokedex. Did you mean: {suggestions}?')

    @classmethod
    def from_csv(cls, csv_line):
        properties = csv_line.strip().split(',')
        pokemon = cls(properties[0], properties[1], properties[2])
        pokemon.evs = PokemonStats(*[int(prop) for prop in properties[3:9]], max_val=252, max_total=510)
        pokemon.ivs_min = PokemonStats(*[int(prop) for prop in properties[9:15]])
        pokemon.ivs_max = PokemonStats(*[int(prop) for prop in properties[15:21]])
        return pokemon

    @classmethod
    def from_dict(cls, in_dict: dict):
        pokemon = cls(in_dict['name'], in_dict['nature'], in_dict['nickname'])
        pokemon.evs = PokemonStats.from_dict({key.split('.')[-1]: val for key, val in in_dict.items() if 'evs.' in key}, max_val=252, max_total=510)
        pokemon.ivs_min = PokemonStats.from_dict({key.split('.')[-1]: val for key, val in in_dict.items() if 'ivs_min.' in key})
        pokemon.ivs_max = PokemonStats.from_dict({key.split('.')[-1]: val for key, val in in_dict.items() if 'ivs_max.' in key})
        return pokemon

    def change_evolution(self, new_name: str):
        try:
            evolutions = pokemondb.get_evolutions(self._name)
        except scrapers.SuggestionException:
            raise PokemonTrackingException(f'Pokemon {self._name} was not found in the Pokedex. It is possible the data has been corrupted.')

        if new_name.lower() not in [e.lower() for e in evolutions]:
            raise PokemonNotFoundException(f'Pokemon {new_name} is not an evolution of {self._name}. ' +
                f'All possible evolutions are: {", ".join(evolutions)}.' if len(evolutions) > 0 else f'There are no evolutions for {self._name}.')
        new_name = new_name.capitalize()

        try:
            self.base_stats = pokemondb.get_base_stats(new_name)
        except scrapers.SuggestionException:
            raise PokemonTrackingException(f'Pokemon {new_name} was not found in the Pokedex but was found in evolution list. Weird.')
        self._name = new_name

    def to_csv(self):
        return f'{self._name},{self._nature_name},{self.nickname},{self.evs.to_csv()},{self.ivs_min.to_csv()},{self.ivs_max.to_csv()}'

    def to_dict(self):
        poke_dict = {
            'name': self._name,
            'nature': self._nature_name,
            'nickname': self.nickname,
        }
        for key, val in self.evs.to_dict().items():
            poke_dict[f'evs.{key}'] = val
        for key, val in self.ivs_min.to_dict().items():
            poke_dict[f'ivs_min.{key}'] = val
        for key, val in self.ivs_max.to_dict().items():
            poke_dict[f'ivs_max.{key}'] = val
        return poke_dict
        

    def get_name(self):
        name = self._name
        if self.nickname:
            name += f' ({self.nickname})'
        return name

    def set_ivs(self, ivs_min, ivs_max):
        self.ivs_min = ivs_min
        self.ivs_max = ivs_max

    def set_evs(self, evs: PokemonStats):
        try:
            evs.set_max_stat_val(252)
            evs.set_max_total_val(510)
        except PokemonStatsError as e:
            raise PokemonTrackingException(f'Failed to set new EVs. Error: {e}')
        self.evs = evs

    def set_nature(self, nature):
        self._nature_name = nature.capitalize()
        self.nature = _natures_map[self._nature_name.lower()]

    def compute_stats_min_max(self, level):
        remaining_evs = 510 - self.evs.total
        evs_rem = PokemonStats(remaining_evs, remaining_evs, remaining_evs, remaining_evs, remaining_evs, remaining_evs)
        ev_copy_max_stats = PokemonStats.from_obj(self.evs)
        ev_copy_max_total = PokemonStats.from_obj(self.evs)
        ev_copy_max_stats.set_max_total_val(60000)
        ev_copy_max_stats += evs_rem
        ev_copy_max_total += evs_rem

        # Compute stats with min (current EV's + min IV's)
        # Compute stats with maximum possible stat value (max EV's in each stat + max IV's)
        # Compute stats with to determine max possible total value (max EV's with 510 total cap + max IV's)
        min_stats = compute_stats(self.base_stats, self.evs, self.ivs_min, self.nature, level)
        max_stats = compute_stats(self.base_stats, ev_copy_max_stats, self.ivs_max, self.nature, level)
        max_total = compute_stats(self.base_stats, ev_copy_max_total, self.ivs_max, self.nature, level)
        max_stats.total = max_total.total
        return (min_stats, max_stats)

class _PokemonTrackingBase:
    def __init__(self):
        self.pokemon = {} # type: dict[str, list[Pokemon]]
        self.load_state()

    def load_state(self):
        raise NotImplementedError('Method "load_state" has not been implemented.')

    def save_state(self, user):
        raise NotImplementedError('Method "save_state" has not been implemented.')

    def to_dict(self):
        return {(user, i): self.pokemon[user][i].to_dict() for user in self.pokemon for i in range(len(self.pokemon[user]))}

    def __check_user(self, user):
        if user not in self.pokemon:
            raise UserNotFoundException('No pokemon tracked for current user.')

    def __check_pokemon_id(self, user, pokemon_id):
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')

    def get_full_name_str(self, user, pokemon_id):
        return f'{pokemon_id}: {self.pokemon[user][pokemon_id].get_name()}'

    def add_pokemon_obj(self, user, pokemon: Pokemon, idx = 0xFFFFFFFF) -> int:
        if user not in self.pokemon:
            self.pokemon[user] = []
        self.pokemon[user].insert(idx, pokemon)
        self.save_state(user)
        return len(self.pokemon[user]) - 1 if idx >= len(self.pokemon[user]) else idx

    def add_pokemon(self, user, pokemon_name, nature, nickname = '', idx = 0xFFFFFFFF) -> int:
        return self.add_pokemon_obj(user, Pokemon(pokemon_name, nature, nickname), idx)

    def add_pokemon_obj_str(self, user, pokemon: Pokemon, idx = 0xFFFFFFFF) -> str:
        self.add_pokemon_obj(user, pokemon, idx)
        return self.get_all_pokemon(user)

    def remove_pokemon(self, user, pokemon_id) -> Pokemon:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        pokemon = self.pokemon[user].pop(pokemon_id)
        if len(self.pokemon[user]) == 0:
            del self.pokemon[user]
        self.save_state(user)
        return pokemon

    def remove_pokemon_str(self, user, pokemon_id) -> str:
        self.remove_pokemon(user, pokemon_id)
        return self.get_all_pokemon(user)

    def get_all_pokemon(self, user) -> str:
        self.__check_user(user)
        poke_list = ''
        for i in range(len(self.pokemon[user])):
            poke_list += f'{self.get_full_name_str(user, i)}\n'
        return poke_list

    def get_pokemon_name(self, user, pokemon_id) -> str:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return self.pokemon[user][pokemon_id]._name

    def get_evs(self, user, pokemon_id) -> PokemonStats:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return self.pokemon[user][pokemon_id].evs

    def get_evs_str(self, user, pokemon_id) -> str:
        evs = self.get_evs(user, pokemon_id)
        return f'**{self.get_full_name_str(user, pokemon_id)}: EVs**\n{evs}'

    def set_evs(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> PokemonStats:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        evs = PokemonStats(hp, attack, defense, sp_atk, sp_def, speed)
        self.pokemon[user][pokemon_id].set_evs(evs)
        self.save_state(user)
        return self.pokemon[user][pokemon_id].evs

    def set_evs_str(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> str:
        evs = self.set_evs(user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed)
        return f'**{self.get_full_name_str(user, pokemon_id)}: EVs**\n{evs}'

    def set_evs_multiple_pokemon(self, user, pokemon_id_list, evs_list) -> list[PokemonStats]:
        self.__check_user(user)

        # First verify all ids
        for pokemon_id in pokemon_id_list:
            self.__check_pokemon_id(user, pokemon_id)

        # Verify the list lengths match
        if len(pokemon_id_list) != len(evs_list):
            raise PokemonTrackingException(f'Number of provided ids ({len(pokemon_id_list)}) is not equal to the number of provided evs ({len(evs_list)}).')

        # Add new EV's after IDs are verified
        new_evs = []
        for i in range(len(pokemon_id_list)):
            self.pokemon[user][pokemon_id_list[i]].set_evs(evs_list[i])
            new_evs.append(self.pokemon[user][pokemon_id_list[i]])
        self.save_state(user)
        return new_evs

    def set_evs_multiple_pokemon_str(self, user, pokemon_id_list, evs_list) -> str:
        self.set_evs_multiple_pokemon(user, pokemon_id_list, evs_list)
        pokemon_id_list = list(set(pokemon_id_list))
        responses = []
        for pokemon_id in pokemon_id_list:
            responses.append(f'**{self.get_full_name_str(user, pokemon_id)}: EVs**\n{self.pokemon[user][pokemon_id].evs}')
        return "\n\n".join(responses)

    def get_ivs(self, user, pokemon_id) -> tuple[PokemonStats, PokemonStats]:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return (self.pokemon[user][pokemon_id].ivs_min, self.pokemon[user][pokemon_id].ivs_max)

    def get_ivs_str(self, user, pokemon_id) -> str:
        ivs_min, ivs_max = self.get_ivs(user, pokemon_id)
        return f'**{self.get_full_name_str(user, pokemon_id)}: IVs**\n{get_stat_range_str(ivs_min, ivs_max)}'

    def get_base_stats(self, user, pokemon_id) -> PokemonStats:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return self.pokemon[user][pokemon_id].base_stats

    def get_base_stats_str(self, user, pokemon_id) -> str:
        base_stats = self.get_base_stats(user, pokemon_id)
        return f'**{self.get_full_name_str(user, pokemon_id)}: Base Stats**\n{base_stats}'

    def set_ivs(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> tuple[PokemonStats, PokemonStats]:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)

        ivs = [stat.lower().replace(' ', '') for stat in [hp, attack, defense, sp_atk, sp_def, speed]]
        try:
            min_ivs = PokemonStats(*[_iv_name_map[name][0] for name in ivs])
            max_ivs = PokemonStats(*[_iv_name_map[name][1] for name in ivs])
        except KeyError:
            raise PokemonTrackingException(f'Failed to determine IVs from provided keywords. IVs must be one of {list(_iv_name_map.keys())}.')

        self.pokemon[user][pokemon_id].set_ivs(min_ivs, max_ivs)
        self.save_state(user)
        return (min_ivs, max_ivs)

    def set_ivs_str(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> str:
        ivs_min, ivs_max = self.set_ivs(user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed)
        return f'**{self.get_full_name_str(user, pokemon_id)}: IVs**\n{get_stat_range_str(ivs_min, ivs_max)}'

    def set_ivs_exact(self, user, pokemon_id, min_ivs, max_ivs) -> tuple[PokemonStats, PokemonStats]:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)

        self.pokemon[user][pokemon_id].set_ivs(min_ivs, max_ivs)
        self.save_state(user)
        return (min_ivs, max_ivs)

    def set_ivs_exact_str(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> str:
        ivs_min, ivs_max = self.set_ivs_exact(user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed)
        return f'**{self.get_full_name_str(user, pokemon_id)}: IVs**\n{get_stat_range_str(ivs_min, ivs_max)}'

    def get_pokemon_stats(self, user, pokemon_id, level) -> tuple[PokemonStats, PokemonStats]:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return self.pokemon[user][pokemon_id].compute_stats_min_max(level)

    def get_pokemon_stats_str(self, user, pokemon_id, level) -> str:
        stats_min, stats_max = self.get_pokemon_stats(user, pokemon_id, level)
        return f'**{self.get_full_name_str(user, pokemon_id)}: Level {level} Stats**\n{get_stat_range_str(stats_min, stats_max)}'

    def change_evolution(self, user, pokemon_id, new_pokemon_name) -> str:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        self.pokemon[user][pokemon_id].change_evolution(new_pokemon_name)
        self.save_state(user)
        return self.get_full_name_str(user, pokemon_id)

    def add_defeated_pokemon(self, user, defeated_pokemon_name, pokemon_id_list) -> list[PokemonStats]:
        pokemon_id_list = list(set(pokemon_id_list))
        self.__check_user(user)
        ev_yield = pokemondb.get_ev_yield_as_stats(defeated_pokemon_name)
        evs_list = []

        # First verify all ids
        for pokemon_id in pokemon_id_list:
            self.__check_pokemon_id(user, pokemon_id)

        # Add new EV's after IDs are verified
        for pokemon_id in pokemon_id_list:
            self.pokemon[user][pokemon_id].evs += ev_yield
            evs_list.append(self.pokemon[user][pokemon_id].evs)
        self.save_state(user)
        return evs_list

    def add_defeated_pokemon_str(self, user, defeated_pokemon_name, pokemon_id_list) -> str:
        pokemon_id_list = list(set(pokemon_id_list))
        evs_list = self.add_defeated_pokemon(user, defeated_pokemon_name, pokemon_id_list)
        responses = []
        if len(pokemon_id_list) != len(evs_list):
            raise PokemonTrackingException('Pokemon ID list size does not match EV list size.')
        for i in range(len(pokemon_id_list)):
            responses.append(f'**{self.get_full_name_str(user, pokemon_id_list[i])}: EVs**\n{evs_list[i]}')
        return '\n\n'.join(responses)

    def consume_ev_vitamin(self, user, pokemon_id, vitamin, count=1):
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        try:
            ev_change = _vitamins_map[vitamin.lower()]
        except KeyError:
            raise PokemonTrackingException(f'Failed to find EV changing vitamin with name {vitamin}. Options are: {list(_vitamins_map.keys())}.')

        for _i in range(count):
            self.pokemon[user][pokemon_id].evs += ev_change
        self.save_state(user)
        return self.pokemon[user][pokemon_id].evs

    def consume_ev_vitamin_str(self, user, pokemon_id, vitamin, count=1):
        return f'**{self.get_full_name_str(user, pokemon_id)}: EVs**\n{self.consume_ev_vitamin(user, pokemon_id, vitamin, count)}'

    def consume_ev_berry(self, user, pokemon_id, berry, count=1):
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        try:
            ev_change = _berries_map[berry.lower()]
        except KeyError:
            raise PokemonTrackingException(f'Failed to find EV changing berry with name {berry}. Options are: {list(_berries_map.keys())}.')

        for _i in range(count):
            self.pokemon[user][pokemon_id].evs += ev_change
        self.save_state(user)
        return self.pokemon[user][pokemon_id].evs

    def consume_ev_berry_str(self, user, pokemon_id, berry, count=1):
        return f'**{self.get_full_name_str(user, pokemon_id)}: EVs**\n{self.consume_ev_berry(user, pokemon_id, berry, count)}'

    def get_nature(self, user, pokemon_id) -> str:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return self.pokemon[user][pokemon_id]._nature_name

    def get_nature_str(self, user, pokemon_id) -> str:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        return f'{self.get_full_name_str(user, pokemon_id)}: **{self.pokemon[user][pokemon_id]._nature_name}**\n{self.pokemon[user][pokemon_id].nature}'

    def set_nature_str(self, user, pokemon_id, nature) -> str:
        self.__check_user(user)
        self.__check_pokemon_id(user, pokemon_id)
        self.pokemon[user][pokemon_id].set_nature(nature)
        self.save_state(user)
        return f'{self.get_full_name_str(user, pokemon_id)}: **{self.pokemon[user][pokemon_id]._nature_name}**\n{self.pokemon[user][pokemon_id].nature}'
