import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import Text
import  sqlalchemy.exc as sql_exc

import tracking.sprint as sprintrack

class SprintTrackingSQL(sprintrack.SprintTracker):
    __pb_database_name = 'wpm_pb_test'

    def __init__(self, *args, **kwargs):
        try:
            database_url = os.environ['SQL_DATABASE_URL']
        except:
            raise sprintrack.SprintError('Failed to find SQL_DATABASE_URL environment variable.')

        try:
            self.__pb_database_name = os.environ['SPRINTRACK_PB_DB_NAME']
        except:
            self.__pb_database_name = SprintTrackingSQL.__pb_database_name
            print(f'Failed to find database name from environment variable SPRINTRACK_PB_DB_NAME, using {self.__pb_database_name} as default.')

        self.__engine = create_engine(database_url, echo=False)
        super().__init__(*args, **kwargs)

    def load_state(self):
        try:
            df = pd.read_sql(f"SELECT * FROM {self.__pb_database_name}", self.__engine)
            for index, row in df.iterrows():
                print(row)
                self.add_pb_from_dict(dict(row))
        except sql_exc.ProgrammingError:
            print(f'Failed to read from table {self.__pb_database_name}.')

    def save_state(self):
        sprint_dict = self.to_dict()
        pb_df = pd.DataFrame.from_records(sprint_dict['pbs'], index='user')
        pb_df.to_sql(self.__pb_database_name, con=self.__engine, if_exists='replace', dtype={'user': Text()})
