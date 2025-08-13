import discord
from discord.ext import commands
import os
from constants import ROLES
import json

class FilesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("files", exist_ok=True)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.has_any_role(ROLES.TOTALLY_MOD)
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
    @commands.has_permissions(manage_messages=True)
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def deletefile(self, ctx, filename: str): 
        """Deletes a saved file."""
        file_path = f"files/{filename}"
        if os.path.exists(file_path):
            os.remove(file_path)
            await ctx.send(f"Deleted `{filename}`.")
        else:
            await ctx.send("File not found.")

    @commands.command()
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def listfiles(self, ctx): 
        """Lists all saved files."""
        files = os.listdir("files")
        if not files:
            await ctx.send("No files found.")
            return

        file_list = "\n".join(files)
        await ctx.send(f"Saved files:\n{file_list}")
        

    @commands.command()
    @commands.has_permissions(manage_messages=True) 
    @commands.has_any_role(ROLES.TOTALLY_MOD)
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

    @commands.command()
    @commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
    async def jsons(self, ctx):
        """Lists all JSON files in the current directory."""
        files = [f for f in os.listdir('.') if f.endswith('.json')]
        if files:
            await ctx.send("📄 JSON files:\n" + '\n'.join(files))
        else:
            await ctx.send("No JSON files found.")

    @commands.command(aliases=["fetchjson", "getjson", "json"])
    @commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
    async def fetch(self, ctx, *, filename):
        """Sends the JSON file by filename (extension optional)."""
        file_path = filename if filename.endswith('.json') else f"{filename}.json"
        
        if os.path.exists(file_path):
            await ctx.send(file=discord.File(file_path))
        else:
            await ctx.send("JSON file not found.")
    @commands.command(aliases=["cat"])
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def file(self, ctx: commands.Context, *, filename: str):
        """Sends any random file (doesn't even have to be in the project dir)"""
        if os.path.exists(filename):
            await ctx.send(file=discord.File(filename))
        else:
            await ctx.send("File not found.")
    @commands.command(aliases=["wipejson", "clearjson", "resetjson"])
    @commands.has_any_role(ROLES.TOTALLY_MOD, "happy")
    async def wipe(self, ctx, *, filename):
        """Wipes the contents of a JSON file (leaves it as {})."""
        file_path = filename if filename.endswith('.json') else f"{filename}.json"

        if os.path.exists(file_path):
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)
                await ctx.send(f"✅ `{file_path}` has been wiped and now contains an empty JSON object.")
            except Exception as e:
                await ctx.send(f"⚠️ Failed to wipe `{file_path}`.\nError: `{type(e).__name__}` - {e}")
        else:
            await ctx.send("❌ JSON file not found.")



# Required function to load this cog
async def setup(bot):
    await bot.add_cog(FilesCog(bot))