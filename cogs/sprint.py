import time
import random
from discord.ext import commands

import tracking.sprint as sprinter

class SprintCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sprint_tracker = sprinter.SprintTracker(self.sprint_started_cb, self.sprint_completed_cb, self.sprint_tally_cb, self.sprint_canceled_cb)
        self.cancel_emojis = [
            '\N{UNAMUSED FACE}',
            '\N{FACE WITH ROLLING EYES}',
            "\U0001F62E\U0000200d\U0001F4A8", # face exhaling
            '\U0001F928', # face with raised eyebrow
            '\N{EXPRESSIONLESS FACE}',
        ]
        self.join_emojis = [
            '\U0001F970', # smiling face with hearts
            '\U0001F60D', # smiling face with heart-eyes
            '\U0001F972', # smiling face with tear
        ]

    async def sprint_started_cb(self, ctx, users, duration):
        await ctx.send(
            f"Sprint starting NOW! You have {f'{duration} seconds' if duration <= 60 else f'{int(duration / 60)} minutes'}.\n" +
            " ".join([f"<@{user}>" for user in users])
        )

    async def sprint_completed_cb(self, ctx, users, tally_time):
        print('Complete cb!')
        await ctx.send(
            f"Pencils down! Computers powered off! Your time is up! " +
            f"You have {f'{tally_time} seconds' if tally_time <= 60 else f'{int(tally_time / 60)} minutes'} to enter your final word counts. " +
            f"Use command `!wc <word_count>` to enter your final word count.\n" +
            " ".join([f"<@{user}>" for user in users])
        )

    async def sprint_tally_cb(self, ctx, user_results_sorted, duration):
        results_str = ""
        place = 1
        for result in user_results_sorted:
            results_str += f"{place}. <@{result[0]}> - {result[1]} words ({f'{result[1] / duration} wps' if duration <= 60 else f'{result[1] * 60 / duration} wpm'})\n"
            place += 1
        await ctx.send(f'Results are in:\n{results_str}\nCongratulations to all participants! Good work!')

    async def sprint_canceled_cb(self, ctx, users):
        await ctx.send(
            f"Sorry to say, this sprint is no more. Cancelled by <@{ctx.message.author.id}> {self.cancel_emojis[random.randint(0, len(self.cancel_emojis) - 1)]}\n" +
            " ".join([f"<@{user}>" for user in users])
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'SprintCommands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.command("sprint")
    async def start_sprint(self, ctx, *args):
        # Initialize variable defaults
        now = int(time.time())
        duration = 15 * 60 # 15 minutes
        duration_init = False
        start_delta = 1 * 60 # in 1 minute
        start_time_init = False

        # Loop arguments
        i = 0
        while i < len(args):
            if args[i] == 'for':
                i += 1
                try:
                    duration = int(args[i]) * 60
                    duration_init = True
                except (IndexError, ValueError):
                    pass
            if args[i] == 'in':
                i += 1
                try:
                    start_delta = int(args[i]) * 60
                    start_time_init = True
                except (IndexError, ValueError):
                    pass
            elif args[i].isnumeric():
                if not duration_init:
                    duration = int(args[i]) * 60
                    duration_init = True
                elif not start_time_init:
                    start_delta = int(args[i]) * 60
                    start_time_init = True
            i += 1

        try:
            self.sprint_tracker.start_sprint(duration, start_delta + now, 60, callback_data=ctx)
            await ctx.send(
                f"**TIME TO JOIN Y'ALL**\n"
                f"A brand new sprint is starting in {f'{start_delta} seconds' if start_delta <= 60 else f'{int(start_delta / 60)} minutes'}. "
                f"You gotta type `!join N` to join with a starting word count of N, or simply `!join` for a starting word count of 0."
            )
        except sprinter.SprintStateError as e:
            await ctx.send(str(e))

    @commands.command("cancel")
    async def cancel_sprint(self, ctx):
        try:
            self.sprint_tracker.cancel_sprint()
        except sprinter.SprintStateError as e:
            await ctx.send(str(e))

    @commands.command("join")
    async def join_sprint(self, ctx, *args):
        # Parse arguments
        starting_wc = 0
        for arg in args:
            if arg.isnumeric():
                starting_wc = int(arg)

        try:
            self.sprint_tracker.join_sprint(ctx.message.author.id, starting_wc)
            await ctx.send(
                f'<@{ctx.message.author.id}> joined the sprint with a starting word count of {starting_wc} {self.join_emojis[random.randint(0, len(self.join_emojis) - 1)]}'
            )
        except sprinter.SprintStateError as e:
            await ctx.send(str(e))

    @commands.command("wc")
    async def word_count(self, ctx, word_count: int):
        try:
            self.sprint_tracker.final_word_count(ctx.message.author.id, word_count)
            await ctx.send(
                f'<@{ctx.message.author.id}> Updated final word count to {word_count} words.'
            )
        except (sprinter.SprintStateError, sprinter.UserNotInSprintError) as e:
            await ctx.send(str(e))

def setup(bot):
    bot.add_cog(SprintCommands(bot))
