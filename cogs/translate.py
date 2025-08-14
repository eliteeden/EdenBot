import discord
from discord.ext import commands
import requests

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='translate', aliases=['duo', 'english', "gtl"])
    async def translate(self, ctx, target_lang: str, *, text: str):
        """Translates text to the target language using LibreTranslate."""
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "auto",
            "target": target_lang,
            "format": "text"
        }

        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            translated_text = response.json().get("translatedText")

            if translated_text:
                await ctx.send(f"**Translated:** {translated_text}")
            else:
                await ctx.send("Translation failed. Try again.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Error: {e}")
    
    @commands.command(name='translate_reply', aliases=['tr_reply', "tr", "engpls"])
    async def translate_reply(self, ctx, target_lang: str):
        """Translates the replied-to message to the target language."""
        # Check if the command is used in reply to another message
        if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
            original_message = ctx.message.reference.resolved
            text_to_translate = original_message.content

            url = "https://libretranslate.de/translate"
            payload = {
                "q": text_to_translate,
                "source": "auto",
                "target": target_lang,
                "format": "text"
            }

            try:
                response = requests.post(url, data=payload)
                response.raise_for_status()
                translated_text = response.json().get("translatedText")

                if translated_text:
                    await ctx.send(f"**Translated:** {translated_text}")
                else:
                    await ctx.send("Translation failed. Try again.")
            except requests.exceptions.RequestException as e:
                await ctx.send(f"Error: {e}")
        else:
            await ctx.send("Please reply to a message you want to translate.")

async def setup(bot):
    """Load the Translate cog."""
    await bot.add_cog(TranslateCog(bot))
    print("Translate cog loaded successfully.")