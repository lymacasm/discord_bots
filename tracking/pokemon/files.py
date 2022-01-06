import os
import pandas as pd
import tracking.pokemon as poketrack

class PokemonTrackingFiles(poketrack._PokemonTrackingBase):
    __file_name = 'pokemon_list.csv'

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        os.makedirs(self.base_dir, exist_ok=True)
        self.__file_name = PokemonTrackingFiles.__file_name
        super().__init__()

    def load_state(self):
        self.pokemon = {}
        try:
            df = pd.read_csv(os.path.join(self.base_dir, f'pokemon_list.csv'))
            for _index, row in df.iterrows():
                user = str(row['user'])
                id = int(row['id'])

                if user not in self.pokemon:
                    self.pokemon[user] = []
                self.pokemon[user].insert(id, poketrack.Pokemon.from_dict(dict(row)))
        except FileNotFoundError as e:
            print(f'Failed to read from file {self.__file_name}.')

    def save_state(self):
        df = pd.DataFrame.from_dict(self.to_dict(), orient='index')
        df.index.set_names(['user', 'id'], inplace=True)
        df.to_csv(os.path.join(self.base_dir, f'pokemon_list.csv'))
