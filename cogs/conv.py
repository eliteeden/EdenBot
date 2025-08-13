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
         # 📏 Feet/Inches to CM 
        ft_in_match = re.match(r"^(?:(\d+)ft)?(?:(\d+)in)?$", input)
        if ft_in_match and (ft_in_match.group(1) or ft_in_match.group(2)):
            feet = int(ft_in_match.group(1)) if ft_in_match.group(1) else 0
            inches = int(ft_in_match.group(2)) if ft_in_match.group(2) else 0
            total_inches = feet * 12 + inches
            cm = round(total_inches * 2.54, 2)
            response = f"📏 `{feet} ft {inches} in` ≈ `{cm} cm`"

        # 📏 CM and/or Inches to Feet/Inches
        cm_in_match = re.match(r"^(?:(\d+(?:\.\d+)?)cm)?(?:(\d+(?:\.\d+)?)in)?$", input)
        if cm_in_match and (cm_in_match.group(1) or cm_in_match.group(2)):
            cm = float(cm_in_match.group(1)) if cm_in_match.group(1) else 0
            inches = float(cm_in_match.group(2)) if cm_in_match.group(2) else 0
            total_inches = (cm / 2.54) + inches
            feet = int(total_inches // 12)
            remaining_inches = round(total_inches % 12, 2)
            response = f"📏 `{cm} cm` + `{inches} in` ≈ `{feet} ft {remaining_inches} in`"

        # 🌡️ Celsius to Kelvin
        kelvin_match = re.match(r"^(\d+(?:\.\d+)?)k$", input)
        if kelvin_match:
            kelvin = float(kelvin_match.group(1))
            celsius = round(kelvin - 273.15, 2)
            response = f"🌡️ `{kelvin}K` is `{celsius}°C`"
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
        
        # ⚖️ Kilograms to Pounds
        kg_match = re.match(r"^(\d+(?:\.\d+)?)kg$", input)
        if kg_match:
            kg = float(kg_match.group(1))
            lbs = round(kg * 2.20462, 2)
            response = f"⚖️ `{kg} kg` is `{lbs} lbs`"

        # ⚖️ Pounds to Kilograms
        lbs_match = re.match(r"^(\d+(?:\.\d+)?)lbs?$", input)
        if lbs_match:
            lbs = float(lbs_match.group(1))
            kg = round(lbs * 0.453592, 2)
            response = f"⚖️ `{lbs} lbs` is `{kg} kg`"

        # 📏 Meters to Yards
        m_match = re.match(r"^(\d+(?:\.\d+)?)m$", input)
        if m_match:
            meters = float(m_match.group(1))
            yards = round(meters * 1.09361, 2)
            response = f"📏 `{meters} m` is `{yards} yd`"

        # 📏 Yards to Meters
        yd_match = re.match(r"^(\d+(?:\.\d+)?)yd$", input)
        if yd_match:
            yards = float(yd_match.group(1))
            meters = round(yards * 0.9144, 2)
            response = f"📏 `{yards} yd` is `{meters} m`"

        # 📏 Kilometers to Miles
        km_match = re.match(r"^(\d+(?:\.\d+)?)km$", input)
        if km_match:
            km = float(km_match.group(1))
            miles = round(km * 0.621371, 2)
            response = f"📏 `{km} km` is `{miles} mi`"

        # 📏 Miles to Kilometers
        mi_match = re.match(r"^(\d+(?:\.\d+)?)mi$", input)
        if mi_match:
            miles = float(mi_match.group(1))
            km = round(miles * 1.60934, 2)
            response = f"📏 `{miles} mi` is `{km} km`"

        if response:
            await ctx.send(response)
        else:
            await ctx.send("❓ Couldn't parse input. Try formats like `180cm`, `5ft 7in`, `100F`, or `37C`.")

async def setup(bot):
    """Function to load the ConversionCog."""
    await bot.add_cog(ConversionCog(bot))
    print("ConversionCog has been loaded.")