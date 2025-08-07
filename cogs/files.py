import discord
from discord.ext import commands
import os

class FilesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("files", exist_ok=True)

    @commands.command()
    async def grabfile(self, ctx, channel_id: int = None):
        """Grabs the most recent attachment from a specified channel."""
        if channel_id == None:
            channel = ctx.channel
        else:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send("Channel not found.")
                return

        async for message in channel.history(limit=50):
            if message.attachments:
                attachment = message.attachments[0]
                file_name = f"files/{attachment.filename}"

                await attachment.save(file_name)
                await ctx.send(f"Saved `{attachment.filename}` from <#{channel_id}>.")
                return

        await ctx.send("No attachments found in recent messages.")

    @commands.command()
    async def sendfile(self, ctx, channelID: int = None, filename: str = None):
        """Sends a previously saved file."""
        if filename is None:
            await ctx.send("Please specify a filename.")
            return

        file_path = f"files/{filename}"

        if not os.path.exists(file_path):
            await ctx.send("File not found. Use `!grabfile` first.")
            return

        if channelID is None:
            channel = ctx.channel
        else:
            channel = self.bot.get_channel(channelID)
            if not channel:
                await ctx.send("Channel not found.")
                return

        await channel.send(file=discord.File(file_path))

# Required function to load this cog
async def setup(bot):
    await bot.add_cog(FilesCog(bot))