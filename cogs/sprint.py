import os
import time
import random
from discord.ext import commands

import tracking.sprint as sprintrack
import tracking.sprint.factory as sprintrack_factory

class SprintCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.passive_aggressive_emojis = [
            '\N{UNAMUSED FACE}',
            '\N{FACE WITH ROLLING EYES}',
            "\U0001F62E\U0000200d\U0001F4A8", # face exhaling
            '\U0001F928', # face with raised eyebrow
            '\N{EXPRESSIONLESS FACE}',
        ]
        self.happy_emojis = [
            '\U0001F970', # smiling face with hearts
            '\U0001F60D', # smiling face with heart-eyes
            '\U0001F972', # smiling face with tear
        ]
        self.sad_emojis = [
            '\U0001F622', # crying face
            '\U0001F62D', # loudly crying face
            '\U0001F61E', # disappointed face
        ]
        self.bot.help_command.add_custom_cmd_msg('sprint',
            "!sprint start\n  Starts a sprint with default settings (1 minute to join, 15 minute sprint).\n\n" + \
            "!sprint for N in M\n  Starts a sprint for N minutes, giving people M minutes to join.\n\n" + \
            "!sprint cancel\n  Cancels the sprint (sprints can only be canceled prior to sprint completion).\n\n" + \
            "!sprint join W\n  Join the current sprint with a starting word count of W.\n\n" + \
            "!sprint leave\n  Leave the current sprint.\n\n" + \
            "!sprint time\n  Gets the time remaining in the current sprint.\n\n" + \
            "!sprint wc F\n  Provide your final word count. Your sprint word count will be F - W (final word count - join word count).\n\n" + \
            "!sprint status\n  Get your sprint word count for the active sprint. will return F - W (final word count - join word count).\n\n" + \
            "!sprint pb\n  Gets your personal best words per minute from previous sprints."
        )

        # Create sprint tracker
        try:
            SPRINT_TRACKING_TYPE = os.environ['SPRINT_TRACKING_TYPE']
            print(f'Using tracking type of {SPRINT_TRACKING_TYPE}.')
        except:
            print('Failed to find environment variable SPRINT_TRACKING_TYPE. Using SQL as default.')
            SPRINT_TRACKING_TYPE = sprintrack_factory.TrackingTypes.SQL
        self.sprint_tracker = sprintrack_factory.tracking_factory(
            SPRINT_TRACKING_TYPE,
            self.sprint_started_cb,
            self.sprint_completed_cb,
            self.sprint_tally_cb,
            self.sprint_canceled_cb
        ) # type: sprintrack.SprintTracker

    async def sprint_started_cb(self, ctx, users, duration):
        if len(users) > 0:
            await ctx.send(
                f"Sprint starting NOW! You have {f'{duration} seconds' if duration <= 60 else f'{int(duration / 60)} minutes'}.\n" +
                " ".join([f"<@{user}>" for user in users])
            )
        else:
            await ctx.send(
                f"Nobody joined the sprint... {self.sad_emojis[random.randint(0, len(self.sad_emojis) - 1)]}"
            )

    async def sprint_completed_cb(self, ctx, users, tally_time):
        await ctx.send(
            f"Pencils down! Computers powered off! Your time is up! " +
            f"You have {f'{tally_time} seconds' if tally_time <= 60 else f'{int(tally_time / 60)} minutes'} to enter your final word counts. " +
            f"Use command `!sprint wc <word_count>` to enter your final word count.\n" +
            " ".join([f"<@{user}>" for user in users])
        )

    async def sprint_tally_cb(self, ctx, user_results_sorted, duration):
        results_str = ""
        place = 1
        for result in user_results_sorted:
            results_str += f"{place}. <@{result[0]}> - {result[1]} words ({f'{round(result[1] / duration, 1)} wps' if duration <= 60 else f'{round(result[1] * 60 / duration, 1)} wpm'})\n"
            place += 1
        await ctx.send(f'Results are in:\n{results_str}\nCongratulations to all participants! Good work!')

    async def sprint_canceled_cb(self, ctx, users):
        await ctx.send(
            f"Sorry to say, this sprint is no more. Cancelled by <@{self.get_user(ctx)}> {self.passive_aggressive_emojis[random.randint(0, len(self.passive_aggressive_emojis) - 1)]}\n" +
            " ".join([f"<@{user}>" for user in users])
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'SprintCommands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.command("sprint")
    async def sprint_cmd_handler(self, ctx, *args):
        if len(args) > 0:
            cmd = args[0]
            if not cmd.isnumeric():
                args = args[1:]
            if cmd in ["start", "for", "in"] or cmd.isnumeric():
                await self.start_sprint(ctx, *args)
            elif cmd == "cancel":
                await self.cancel_sprint(ctx, *args)
            elif cmd == "join":
                await self.join_sprint(ctx, *args)
            elif cmd == "leave":
                await self.leave_sprint(ctx, *args)
            elif cmd == "time":
                await self.time_remaining(ctx, *args)
            elif cmd == "wc":
                await self.word_count(ctx, *args)
            elif cmd == "status":
                await self.get_sprint_word_count(ctx, *args)
            elif cmd == "pb":
                await self.get_pb(ctx, *args)

    def get_user(self, ctx):
        return str(ctx.message.author.id)

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

        if duration == 0:
            await ctx.send('Sprint must be for at least 1 minute.')
            return

        try:
            self.sprint_tracker.start_sprint(duration, start_delta + now, callback_data=ctx)
            await ctx.send(
                f"**TIME TO JOIN Y'ALL**\n"
                f"A brand new sprint is starting in {f'{start_delta} seconds' if start_delta <= 60 else f'{int(start_delta / 60)} minutes'}. "
                f"You gotta type `!sprint join N` to join with a starting word count of N, or simply `!sprint join` for a starting word count of 0."
            )
        except sprintrack.SprintStateError as e:
            await ctx.send(str(e))

    async def cancel_sprint(self, ctx):
        try:
            self.sprint_tracker.cancel_sprint()
        except sprintrack.SprintStateError as e:
            await ctx.send(str(e))

    async def join_sprint(self, ctx, *args):
        # Parse arguments
        starting_wc = 0
        for arg in args:
            if arg.isnumeric():
                starting_wc = int(arg)

        try:
            self.sprint_tracker.join_sprint(self.get_user(ctx), starting_wc)
            await ctx.send(
                f'<@{self.get_user(ctx)}> joined the sprint with a starting word count of {starting_wc} {self.happy_emojis[random.randint(0, len(self.happy_emojis) - 1)]}'
            )
        except sprintrack.SprintStateError as e:
            await ctx.send(str(e))

    async def leave_sprint(self, ctx, *args):
        try:
            self.sprint_tracker.leave_sprint(self.get_user(ctx))
            await ctx.send(
                f'<@{self.get_user(ctx)}> has left the sprint.'
            )
        except (sprintrack.SprintStateError, sprintrack.UserNotInSprintError) as e:
            await ctx.send(str(e))

    async def time_remaining(self, ctx, *args):
        try:
            end_time = self.sprint_tracker.get_sprint_end_time()
            now = time.time()
            remaining = int(end_time - now) if end_time > now else 0
            await ctx.send(
                f'There is {f"{remaining} seconds" if remaining <= 60 else f"{remaining / 60} minutes"} remaining in the current sprint.'
            )
        except sprintrack.SprintStateError as e:
            await ctx.send(str(e))

    async def word_count(self, ctx, *args):
        # Parse arguments
        final_wc = -1
        for arg in args:
            if arg.isnumeric():
                final_wc = int(arg)

        try:
            final_wc = self.sprint_tracker.final_word_count(self.get_user(ctx), final_wc)
            await ctx.send(
                f"<@{self.get_user(ctx)}>'s final word count has been updated to {final_wc} words."
            )
        except (sprintrack.SprintStateError, sprintrack.UserNotInSprintError) as e:
            await ctx.send(str(e))

    async def get_sprint_word_count(self, ctx, *args):
        try:
            word_count = self.sprint_tracker.get_word_count(self.get_user(ctx))
            await ctx.send(
                f"<@{self.get_user(ctx)}>'s current word count for this sprint is {word_count}."
            )
        except (sprintrack.SprintStateError, sprintrack.UserNotInSprintError) as e:
            await ctx.send(str(e))

    async def get_pb(self, ctx, *args):
        try:
            pb = self.sprint_tracker.get_personal_best(self.get_user(ctx))
            await ctx.send(
                f"<@{self.get_user(ctx)}>'s personal best is {pb} wpm."
            )
        except sprintrack.UserNotFound as e:
            await ctx.send(str(e))

def setup(bot):
    bot.add_cog(SprintCommands(bot))
