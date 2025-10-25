from discord.ext import commands
import webcolors


class ColorCog(commands.Cog):
    """A cog for managing colors."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def closest_color(hex_code):
        try:
            return webcolors.hex_to_name(hex_code)
        except ValueError:  # Convert hex to RGB
            r, g, b = webcolors.hex_to_rgb(hex_code)
            closest_name = min(
                webcolors.names("css3"),
                key=lambda name: (
                    0
                    if webcolors.rgb_to_hex(webcolors.name_to_rgb(name)) == hex_code
                    else
                    # Squared distance
                    (
                        (webcolors.name_to_rgb(name)[0] - r) ** 2
                        + (webcolors.name_to_rgb(name)[1] - g) ** 2
                        + (webcolors.name_to_rgb(name)[2] - b) ** 2
                    )
                ),
            )

        return closest_name

    def color_to_hex(self, name: str) -> str:
        try:
            return webcolors.name_to_hex(name.lower())
        except ValueError:
            hex_code = None
            name = name.lower()
            closest_match = None
            min_diff = float("inf")

            # Convert name to RGB fallback using fuzzy comparison
            for known_name, known_hex in [
                (name, webcolors.name_to_hex(name)) for name in webcolors.names("css3")
            ]:
                try:
                    known_rgb = webcolors.name_to_rgb(known_name)
                    # Just compare string similarity or a basic diff in name length
                    diff = sum(
                        a != b for a, b in zip(name.ljust(len(known_name)), known_name)
                    )
                    if diff < min_diff:
                        min_diff = diff
                        closest_match = known_name
                        hex_code = known_hex
                except ValueError:
                    continue

            return hex_code if hex_code else "Unknown hex"

    @commands.command(name="gethex")
    async def gethex(self, ctx: commands.Context, color: str):
        try:
            if color.startswith("#") or (
                len(color) in {6, 7}
                and all(c in "0123456789abcdefABCDEF" for c in color.strip("#"))
            ):
                # It's a hex code
                color = color if color.startswith("#") else f"#{color}"
                name = self.closest_color(color)
                await ctx.send(f"🎨 The closest color to `{color}` is just **{name}**")
            else:
                # Assume it's a color name
                try:
                    hex_code = webcolors.name_to_hex(color.lower())
                    await ctx.send(
                        f"🧾 **{color}** is just dummy terms for `{hex_code}`"
                    )
                except ValueError:
                    await ctx.send("❌ I have never seen that color before, bozo.")
        except Exception as e:
            await ctx.send(f"Error: {e}")


async def setup(bot: commands.Bot):
    """Function to load the cog."""
    await bot.add_cog(ColorCog(bot)) # type: ignore
    print("ColorCog has been (re-)loaded.")
