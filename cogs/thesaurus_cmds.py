from discord.ext import commands

import scrapers.thesaurus as thesaurus

class ThesaurusCommands(commands.Cog):
    """ Contains commands used to access thesaurus. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'ThesaurusCommands connected as User: {self.bot.user}, ID: {self.bot.user.id}.')

    @commands.command()
    async def synonym(self, ctx, word: str, *args):
        print_word = word
        if len(args) > 0:
            word_list = [word] + list(args)
            word = '+'.join(word_list)
            print_word = ' '.join(word_list)

        # Get synonyms
        try:
            (sucess, results) = thesaurus.get_synonym(word)
        except thesaurus.WebRequestException as e:
            print(f'WebRequestException in get_synonym call: {e}')
            await ctx.send(f'No synonyms found for {print_word}.')
            return
        except thesaurus.WebParseException as e:
            print(f'WebParseException in get_synonym call: {e}')
            await ctx.send(f'Failed to find synonyms for {print_word}. Please contact bot tech for help.')
            return

        # If success is true, results are a list of synonyms. Otherwise, results is a list of word suggestions.
        if sucess:
            await ctx.send(', '.join(results))
        else:
            await ctx.send(f'No synonyms found for {print_word}. Did you mean: {", ".join(results)}?')

    @commands.command()
    async def define(self, ctx, word: str, *args):
        if len(args) > 0:
            await ctx.send(f'One. Word. At. A. Time. *PLEASE*.')
            return

        try:
            result = thesaurus.get_definition(word)
        except thesaurus.WebRequestException as e:
            print(f'WebParseException in get_definition call: {e}')
            await ctx.send(f":bell: Ding dong that spelling is wrong :bell:")
            return

        response = ''
        for type, definitions in result.items():
            response += f"{type}:\n"
            count = 1
            for definition in definitions:
                response += f"\t{count}. {definition}\n"
                count += 1
            definition += "\n"
        await ctx.send(response)

def setup(bot):
    bot.add_cog(ThesaurusCommands(bot))
