import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from ..constants import ROLES




class ConfessCog(commands.Cog):
    @staticmethod
    def load_colors():
        if not os.path.exists("user_colors.json"):
            return {}  # Return an empty dictionary if the file doesn't exist

        try:
            with open("user_colors.json", "r") as file:
                data = json.load(file)
                return data if isinstance(data, dict) else {}  # Ensure it's a dictionary
        except json.JSONDecodeError:
            return {}  # Return an empty dictionary if JSON is invalid

    # Save updated user colors to JSON
    @staticmethod
    def save_colors(data):
        with open("user_colors.json", "w") as file:
            json.dump(data, file, indent=4)

    # Generate a random hex color
    @staticmethod
    def generate_hex_color():
        return f"#{random.randint(0, 0xFFFFFF):06x}"
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_colors = self.load_colors()  # Load colors when the cog is initialized

    @app_commands.command(name="confess", description="Send an anonymous confession")
    async def confess(self, interaction: discord.Interaction, message: str, image: str = ""):
        user_name = str(interaction.user.name)  # Convert username to string for JSON compatibility

        if user_name not in self.user_colors:
            self.user_colors[user_name] = self.generate_hex_color()
            self.save_colors(self.user_colors)  # Save the updated data

        hex_code: str = self.user_colors[user_name]
        embed = discord.Embed(title=f"Anon-{hex_code.removeprefix('#')}".capitalize(), description=message, color=int(hex_code[1:], 16))

        if image != "":
            embed.set_image(url=image)

        await interaction.response.defer(ephemeral=True)  # Prevents errors by deferring the interaction
        await interaction.channel.send(embed=embed)  # type: ignore # Sends the embed without replying to the trigger
        await interaction.delete_original_response()

    
    @commands.command(name="resetconfessions")
    @commands.has_any_role(ROLES.MODERATOR)
    async def reset_confessions(self, ctx: commands.Context):
        """Reset everyone's colors."""
        self.user_colors = {}
        self.save_colors(self.user_colors)  # Save the reset data
        await ctx.send("All user colors have been reset.")
    
    async def cog_load(self):
        self.bot.tree.add_command(self.confess)
        for command in self.get_app_commands():
            self.bot.tree.add_command(command)
        return await super().cog_load()
