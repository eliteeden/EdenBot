import discord
from discord.ext import commands
from setuptools import Command

class UnintroducedRemover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = 123456789012345678  # Replace with your channel ID
        self.role_id = 987654321098765432     # Replace with your role ID

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Trigger condition: specific channel and message contains "Name:"
        if message.channel.id == self.channel_id and "Name:" in message.content:
            guild = message.guild
            member = message.author
            role = guild.get_role(self.role_id)

            # If member has the role, remove it
            if role in member.roles:
                await member.remove_roles(role)
                
                await message.channel.send(f"Role removed from {member.display_name}.")

        # Ensure commands still work
        await self.bot.process_commands(message)

# Setup function to add the Cog
async def setup(bot: commands.Bot):
    """Function to add the IntroCog"""
    await bot.add_cog(UnintroducedRemover(bot))
    print("IntroCog has been loaded.")