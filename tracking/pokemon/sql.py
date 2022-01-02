import os
import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy.exc as sql_exc

import tracking.pokemon as poketrack

class PokemonTrackingSQL(poketrack._PokemonTrackingBase):
    __database_name = 'pokemon_list'

    def __init__(self):
        try:
            database_url = os.environ['DATABASE_URL']
        except:
            raise poketrack.PokemonTrackingException('Failed to find DATABASE_URL environment variable.')
        
        try:
            self.__database_name = os.environ['DATABASE_NAME']
        except:
            self.__database_name = PokemonTrackingSQL.__database_name
            print(f'Failed to find database name from environment variable DATABASE_NAME, using {self.__database_name} as default.')

        self.__engine = create_engine(database_url, echo=False)
        super().__init__()

    def load_state(self):
        self.pokemon = {}
        try:
            df = pd.read_sql(f"SELECT * FROM {self.__database_name}", self.__engine, index_col=['user', 'id'])
            for index, row in df.iterrows():
                user = index[0]
                id = index[1]

                if user not in self.pokemon:
                    self.pokemon[user] = []
                self.pokemon[user].insert(id, poketrack._Pokemon.from_dict(dict(row)))
        except sql_exc.ProgrammingError as e:
            print(f'Failed to read from table {self.__database_name}.')

    def save_state(self, user):
        df = pd.DataFrame.from_dict(self.to_dict(), orient='index')
        df.index.set_names(['user', 'id'], inplace=True)
        df.to_sql(self.__database_name, con=self.__engine, if_exists='replace')
