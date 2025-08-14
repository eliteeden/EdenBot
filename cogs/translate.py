from encodings import aliases
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
    
    @commands.command(name='translate_reply', aliases=['duo_reply', 'english_reply', "gtl_reply", "tr"])
    async def translate_reply(self, ctx, target_lang: str = "en"):
        """Translates the replied-to message to the target language (default: English)."""
        if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
            original_message = ctx.message.reference.resolved
            text_to_translate = original_message.content

            url = "https://libretranslate.de/translate"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "q": text_to_translate,
                "source": "auto",
                "target": target_lang,
                "format": "text"
            }

            try:
                response = requests.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    await ctx.send(f"API error {response.status_code}: {response.text}")
                    return

                data = response.json()
                translated_text = data.get("translatedText")

                if translated_text:
                    await ctx.send(f"**Translated:** {translated_text}")
                else:
                    await ctx.send("Translation failed. No text returned.")
            except requests.exceptions.RequestException as e:
                await ctx.send(f"Request error: {e}")
            except ValueError:
                await ctx.send("Error: Response was not valid JSON.")
        else:
            await ctx.send("Please reply to a message you want to translate.")
async def setup(bot):
    """Load the Translate cog."""
    await bot.add_cog(TranslateCog(bot))
    print("Translate cog loaded successfully.")