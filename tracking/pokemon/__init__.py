from utility.pokemon import PokemonStats, compute_stats
import scrapers
import scrapers.pokemondb as pokemondb

class PokemonTrackingException(Exception):
    pass

class PokemonNotFoundException(PokemonTrackingException):
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

class _Pokemon:
    def __init__(self, pokemon_name, nature, nickname = ''):
        self.__name = pokemon_name
        self.__nature_name = nature.lower()
        self.nickname = nickname
        self.evs = PokemonStats()
        self.ivs_min = PokemonStats(0, 0, 0, 0, 0, 0)
        self.ivs_max = PokemonStats(31, 31, 31, 31, 31, 31)
        self.nature = _natures_map[self.__nature_name]
        try:
            self.base_stats = pokemondb.get_base_stats(pokemon_name)
        except scrapers.SuggestionException as suggestions:
            raise PokemonNotFoundException(f'Pokemon {pokemon_name} was not found in the Pokedex. Did you mean: {suggestions}?')

    @classmethod
    def from_csv(cls, csv_line):
        properties = csv_line.strip().split(',')
        pokemon = cls(properties[0], properties[1], properties[2])
        pokemon.evs = PokemonStats(*[int(prop) for prop in properties[3:9]])
        pokemon.ivs_min = PokemonStats(*[int(prop) for prop in properties[9:15]])
        pokemon.ivs_max = PokemonStats(*[int(prop) for prop in properties[15:21]])
        return pokemon

    def to_csv(self):
        return f'{self.__name},{self.__nature_name},{self.nickname},{self.evs.to_csv()},{self.ivs_min.to_csv()},{self.ivs_max.to_csv()}'

    def get_name(self):
        name = self.__name
        if self.nickname:
            name += f' ({self.nickname})'
        return name

    def set_ivs(self, ivs_min, ivs_max):
        self.ivs_min = ivs_min
        self.ivs_max = ivs_max

    def compute_stats_min_max(self, level):
        min_stats = compute_stats(self.base_stats, self.evs, self.ivs_min, self.nature, level)
        max_stats = compute_stats(self.base_stats, self.evs, self.ivs_max, self.nature, level)
        return (min_stats, max_stats)

class _PokemonTrackingBase:
    def __init__(self):
        self.pokemon = {} # type: dict[str, list[_Pokemon]]
        self.load_state()

    def load_state(self):
        raise NotImplementedError('Method "load_state" has not been implemented.')

    def save_state(self):
        raise NotImplementedError('Method "save_state" has not been implemented.')

    def add_pokemon(self, user, pokemon_name, nature, nickname = '') -> str:
        if user not in self.pokemon:
            self.pokemon[user] = []
        self.pokemon[user].append(_Pokemon(pokemon_name, nature, nickname))
        self.save_state()
        return str(len(self.pokemon[user]) - 1) + ': ' + self.pokemon[user][-1].get_name()

    def get_all_pokemon(self, user) -> str:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        poke_list = ''
        for i in range(len(self.pokemon[user])):
            poke_list += f'{i}: {self.pokemon[user][i].get_name()}\n'
        return poke_list

    def get_evs(self, user, pokemon_id) -> PokemonStats:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')
        return self.pokemon[user][pokemon_id].evs

    def get_ivs(self, user, pokemon_id) -> tuple[PokemonStats, PokemonStats]:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')
        return (self.pokemon[user][pokemon_id].ivs_min, self.pokemon[user][pokemon_id].ivs_max)

    def get_base_stats(self, user, pokemon_id) -> PokemonStats:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')
        return self.pokemon[user][pokemon_id].base_stats

    def set_ivs(self, user, pokemon_id, hp, attack, defense, sp_atk, sp_def, speed) -> tuple[PokemonStats, PokemonStats]:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')

        ivs = [stat.lower().replace(' ', '') for stat in [hp, attack, defense, sp_atk, sp_def, speed]]
        min_ivs = PokemonStats(*[_iv_name_map[name][0] for name in ivs])
        max_ivs = PokemonStats(*[_iv_name_map[name][1] for name in ivs])

        self.pokemon[user][pokemon_id].set_ivs(min_ivs, max_ivs)
        self.save_state()
        return (min_ivs, max_ivs)

    def get_pokemon_stats(self, user, pokemon_id, level) -> tuple[PokemonStats, PokemonStats]:
        if user not in self.pokemon:
            raise PokemonNotFoundException('No pokemon tracked for current user.')
        if pokemon_id >= len(self.pokemon[user]):
            raise PokemonNotFoundException(f'Failed to find any pokemon with ID {pokemon_id}.')
        return self.pokemon[user][pokemon_id].compute_stats_min_max(level)
