from discord.ext import commands
import re

class ConversionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="convert", aliases=["conversion", "unit", "conv"])
    async def convert(self, ctx, *, input: str):
        """Converts between cm/ft/in and Celsius/Fahrenheit."""
        input = input.lower().replace(" ", "")
        response = ""

        # 📏 CM to Feet/Inches
        cm_match = re.match(r"^(\d+(?:\.\d+)?)cm$", input)
        if cm_match:
            cm = float(cm_match.group(1))
            inches_total = cm / 2.54
            feet = int(inches_total // 12)
            inches = round(inches_total % 12, 2)
            response = f"📏 `{cm} cm` is approximately `{feet} ft {inches} in`"

        # 📏 Feet/Inches to CM
        ft_in_match = re.match(r"^(\d+)ft(\d+)in$", input)
        if ft_in_match:
            feet = int(ft_in_match.group(1))
            inches = int(ft_in_match.group(2))
            total_inches = feet * 12 + inches
            cm = round(total_inches * 2.54, 2)
            response = f"📏 `{feet} ft {inches} in` is approximately `{cm} cm`"

        # 🌡️ Celsius to Fahrenheit
        c_match = re.match(r"^(\d+(?:\.\d+)?)c$", input)
        if c_match:
            celsius = float(c_match.group(1))
            fahrenheit = round((celsius * 9/5) + 32, 2)
            response = f"🌡️ `{celsius}°C` is `{fahrenheit}°F`"

        # 🌡️ Fahrenheit to Celsius
        f_match = re.match(r"^(\d+(?:\.\d+)?)f$", input)
        if f_match:
            fahrenheit = float(f_match.group(1))
            celsius = round((fahrenheit - 32) * 5/9, 2)
            response = f"🌡️ `{fahrenheit}°F` is `{celsius}°C`"

        if response:
            await ctx.send(response)
        else:
            await ctx.send("❓ Couldn't parse input. Try formats like `180cm`, `5ft 7in`, `100F`, or `37C`.")

async def setup(bot):
    """Function to load the ConversionCog."""
    await bot.add_cog(ConversionCog(bot))
    print("ConversionCog has been loaded.")