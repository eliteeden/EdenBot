from ast import alias
import discord
from discord.ext import commands
from googletrans import Translator, LANGUAGES

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command(name="translate", aliases=["tr", "tl"])
    async def translate(self, ctx, lang: str, *, text: str):
        """Translates text to the specified language."""
        try:
            translation = self.translator.translate(text, dest=lang)
            await ctx.send(f"**Translated ({lang}):** {translation}")
        except Exception as e:
            await ctx.send(f"Translation error: {e}")

    @commands.command(name="languages", aliases=["langs", "langlist"])
    async def languages(self, ctx):
        """Lists supported languages."""
        lang_list = [f"{code}: {name}" for code, name in LANGUAGES.items()]
        # Discord has a 2000 character limit per message, so split if needed
        chunks = [lang_list[i:i+50] for i in range(0, len(lang_list), 50)]
        for chunk in chunks:
            await ctx.send("\n".join(chunk))

    @commands.command(name="translate_reply", aliases=["tr_reply", "trr"])
    async def translate_reply(self, ctx, lang: str = "en"):
        """Translates the replied-to message to the specified language (default: English)."""
        if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
            original_message = ctx.message.reference.resolved
            text_to_translate = original_message.content

            try:
                translation = self.translator.translate(text_to_translate, dest=lang)
                await ctx.send(f"**Translated ({lang}):** {translation}")
            except Exception as e:
                await ctx.send(f"Translation error: {e}")
        else:
            await ctx.send("Please reply to a message you want to translate.")


async def setup(bot):
    await bot.add_cog(TranslateCog(bot))
    print("Translate cog loaded successfully.")