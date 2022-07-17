from discord.ext import commands

_g_custom_cmd_msgs = {}

class HelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def add_custom_cmd_msg(self, cmd, msg):
        global _g_custom_cmd_msgs
        _g_custom_cmd_msgs[cmd] = msg

    async def send_command_help(self, command):
        global _g_custom_cmd_msgs
        if command.name in _g_custom_cmd_msgs:
            await self.get_destination().send("```" + _g_custom_cmd_msgs[command.name] + "```")
        else:
            await super().send_command_help(command)
