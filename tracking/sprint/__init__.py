import asyncio
import time
import pandas as pd
from typing import Callable

class SprintError(Exception):
    pass

class SprintStateError(SprintError):
    pass

class UserNotFound(SprintError):
    pass

class UserNotInSprintError(UserNotFound):
    pass

class SprintTracker:
    def __init__(
            self, 
            start_callback:Callable[[object, list[str],int],None], 
            end_callback:Callable[[object, list[str],int],None],
            final_tally_callback:Callable[[object, list[tuple[str,int]]],None],
            cancel_callback:Callable[[object, list[str]], None]
        ):
        self.__start_callback = start_callback
        self.__end_callback = end_callback
        self.__final_tally_callback = final_tally_callback
        self.__cancel_callback = cancel_callback
        self.__callback_data = None

        self.__start_task = None
        self.__duration_task = None
        self.__tally_task = None

        # Data
        self.__user_wc = {} # type: dict[str, tuple[int, int]]
        self.__user_pb_wpm = {} # type: dict[str, float]

        self.__duration = 15 * 60
        self.__start_time = 0
        self.__final_tally_time = 120
        self.__sprint_start_time = 0
        self.load_state()

    def load_state(self):
        pass

    def save_state(self):
        pass

    def add_pb_from_dict(self, pb_dict):
        if pb_dict['user'] not in self.__user_pb_wpm or pb_dict['wpm'] > self.__user_pb_wpm[pb_dict['user']]:
            self.__user_pb_wpm[pb_dict['user']] = pb_dict['wpm']

    def to_dict(self):
        return {
            'pbs': [{'user': user, 'wpm': wpm} for user, wpm in self.__user_pb_wpm.items()]
        }

    async def __timer_fn(self, fn):
        try:
            await fn()
        except asyncio.CancelledError:
            if self.__cancel_callback is not None:
                await self.__cancel_callback(self.__callback_data, list(self.__user_wc.keys()))
            self.__start_task = None
            self.__duration_task = None
            self.__tally_task = None
        except:
            from traceback import format_exc
            print(format_exc())

    async def __start_sprint_timer(self):
        now = time.time()
        if self.__start_time > now:
            await asyncio.sleep(self.__start_time - now)
        if self.__start_callback is not None:
            await self.__start_callback(self.__callback_data, list(self.__user_wc.keys()), self.__duration)
        self.__start_task = None

        if len(self.__user_wc) > 0:
            self.__duration_task = asyncio.ensure_future(self.__timer_fn(self.__end_sprint_timer))
        
    async def __end_sprint_timer(self):
        self.__sprint_start_time = time.time()
        await asyncio.sleep(self.__duration)
        if self.__end_callback is not None:
            await self.__end_callback(self.__callback_data, list(self.__user_wc.keys()), self.__final_tally_time)
        self.__duration_task = None
        self.__tally_task = asyncio.ensure_future(self.__timer_fn(self.__final_tally_timer))

    async def __final_tally_timer(self):
        await asyncio.sleep(self.__final_tally_time)
        if self.__final_tally_callback is not None:
            await self.__final_tally_callback(
                    self.__callback_data,
                    sorted([(key, val[1] - val[0]) for key, val in self.__user_wc.items()], key=lambda r: r[1], reverse=True),
                    self.__duration
                )

        # Update personal best info
        for user, word_counts in self.__user_wc.items():
            wpm = (word_counts[1] - word_counts[0]) * 60 / self.__duration
            if user not in self.__user_pb_wpm:
                self.__user_pb_wpm[user] = wpm
            elif wpm > self.__user_pb_wpm[user]:
                self.__user_pb_wpm[user] = wpm
        self.__user_wc = {}
        self.save_state()
        self.__tally_task = None

    def start_sprint(self, duration:int, start_time:int, final_tally_time=120, callback_data=None):
        if any([t is not None for t in [self.__start_task, self.__duration_task]]):
            raise SprintStateError("There's already an active sprint.")
        if self.__tally_task is not None:
            raise SprintStateError("Cannot start sprint until previous sprint results come in.")

        self.__duration = duration
        self.__start_time = start_time
        self.__final_tally_time = final_tally_time
        self.__callback_data = callback_data

        self.__start_task = asyncio.ensure_future(self.__timer_fn(self.__start_sprint_timer))

    def cancel_sprint(self):
        if all([t is None for t in [self.__start_task, self.__duration_task]]):
            raise SprintStateError("There's currently no active sprint.")

        for t in [self.__start_task, self.__duration_task]:
            if t is not None:
                t.cancel()

    def join_sprint(self, user_id, start_wc):
        if all([t is None for t in [self.__start_task, self.__duration_task]]):
            raise SprintStateError("There's currently no active sprint.")

        self.__user_wc[user_id] = (start_wc,start_wc)

    def leave_sprint(self, user_id):
        if all([t is None for t in [self.__start_task, self.__duration_task, self.__tally_task]]):
            raise SprintStateError("There's currently no active sprint.")
        if user_id not in self.__user_wc:
            raise UserNotInSprintError(f"<@{user_id}> is not part of the sprint.")

        del self.__user_wc[user_id]

    def get_sprint_end_time(self):
        if self.__duration_task is None:
            if self.__start_task is not None:
                raise SprintStateError("The sprint hasn't started yet.")
            elif self.__tally_task is not None:
                raise SprintStateError("The sprint has finished. Tallying results.")
            raise SprintStateError("There's currently no active sprint.")

        return self.__sprint_start_time + self.__duration

    def final_word_count(self, user_id, end_wc):
        if all([t is None for t in [self.__duration_task, self.__tally_task]]):
            raise SprintStateError("There's currently no completed sprint to add your tally to.")
        if user_id not in self.__user_wc:
            raise UserNotInSprintError(f"<@{user_id}> was not part of the sprint.")
        if end_wc < 0:
            end_wc = self.__user_wc[user_id][0]

        self.__user_wc[user_id] = (self.__user_wc[user_id][0], end_wc)
        return end_wc

    def get_word_count(self, user_id):
        if all([t is None for t in [self.__start_task, self.__duration_task, self.__tally_task]]):
            raise SprintStateError("There's currently no active sprint.")
        if user_id not in self.__user_wc:
            raise UserNotInSprintError(f"<@{user_id}> is not part of the sprint.")

        return self.__user_wc[user_id][1] - self.__user_wc[user_id][0]

    def get_personal_best(self, user_id):
        print(self.__user_pb_wpm)
        print(user_id)
        if user_id not in self.__user_pb_wpm:
            raise UserNotFound(f'<@{user_id}> has not participated in any sprints on record.')
        return self.__user_pb_wpm[user_id]

    def get_active_sprint_users(self):
        return list(self.__user_wc.keys())
