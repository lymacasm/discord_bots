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
        # Validate args
        print_word = word
        if len(args) > 0:
            word_list = [word] + list(args)
            word = '+'.join(word_list)
            print_word = ' '.join(word_list)

        # Get synonyms
        try:
            (sucess, results) = thesaurus.get_synonym(word)
        except thesaurus.WebRequestException as e:
            with open('err.log', 'a') as f:
                f.write(f'WebRequestException in get_synonym call: {e}\n')
            await ctx.send(f'No synonyms found for {print_word}.')
            return
        except thesaurus.WebParseException as e:
            with open('err.log', 'a') as f:
                f.write(f'WebParseException in get_synonym call: {e}\n')
            await ctx.send(f'Failed to find synonyms for {print_word}. Please contact bot tech for help.')
            return

        # If success is true, results are a list of synonyms. Otherwise, results is a list of word suggestions.
        if sucess:
            await ctx.send(', '.join(results))
        else:
            await ctx.send(f'No synonyms found for {print_word}. Did you mean: {", ".join(results)}?')

def setup(bot):
    bot.add_cog(ThesaurusCommands(bot))
