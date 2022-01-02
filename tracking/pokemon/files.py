import os
import tracking.pokemon as poketrack

class PokemonTrackingFiles(poketrack._PokemonTrackingBase):
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
        os.makedirs(self.base_dir, exist_ok=True)
        super().__init__()

    def load_state(self):
        all_files = [f for f in os.listdir(self.base_dir) if os.path.isfile(os.path.join(self.base_dir, f))]
        for file in all_files:
            full_path = os.path.join(self.base_dir, file)
            with open(full_path) as f:
                user = file.split('.')[0].replace('pokemon_', '')
                self.pokemon[user] = []
                for line in f.readlines():
                    self.pokemon[user].append(poketrack._Pokemon.from_csv(line))

    def save_state(self, user):
        with open(os.path.join(self.base_dir, f'pokemon_{user}.csv'), 'w') as f:
            for pokemon in self.pokemon[user]:
                f.write(pokemon.to_csv() + '\n')
