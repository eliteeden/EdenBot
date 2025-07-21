from asyncio import subprocess
from constants import ROLES
from discord.ext import commands
import os

class DevCog(commands.Cog):
    """Some development and testing commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.startup: int = 0 # this will get changed in the on_ready event

    @commands.command(name='sync')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
    
    # Cog commands
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    @commands.command(name='cogs')
    async def cogs(self, ctx: commands.Context):
        await ctx.send("Loaded cogs: `" + "`, `".join(self.bot.cogs.keys()) + "`")
        # List available cogs in the cogs directory
        cogs = os.listdir("cogs")
        send_cogs = []
        for cog in cogs:
            if cog.endswith(".py"):
                cog_name = cog[:-3]
                send_cogs.append(cog_name)
        await ctx.send("Available cogs: `" + "`, `".join(send_cogs) + "`")
    @cogs.error
    async def cogs_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("Trust me, you can't untangle the spaghetti inside.")
        else:
            await ctx.send(f"An unexpected error occurred: {error}")
    @commands.command(name='reload')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def reload(self, ctx: commands.Context, cog: str):
        """Reloads a specific cog."""
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(f"{cog} cog reloaded successfully!")
        except Exception as e:
            await ctx.send(f"Failed to reload {cog} cog: {e}")
            print(e)
    @reload.error
    async def reload_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handles errors for the reload command."""
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("buzz off butterfingers, only an elite few can tinker with me like that")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.send("The specified cog does not exist.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("What do you want me to do, reload *everything*?")
        else:
            await ctx.send(f"An unexpected error occurred: {error}")
    @commands.command(name='load')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def load(self, ctx: commands.Context, cog: str):
        """Loads a specific cog."""
        try:
            await self.bot.load_extension(f"cogs.{cog}")
            await ctx.send(f"{cog} cog loaded successfully!")
        except Exception as e:
            await ctx.send(f"Failed to load {cog} cog: {e}")
            print(e)
    @load.error
    async def load_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handles errors for the load command."""
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("what do you even mean to do with that command, filthy peasant?")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.send("The specified cog does not exist.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("What even is there to load?")
        else:
            await ctx.send(f"An unexpected error occurred: {error}")

    @commands.command(name='nohup')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def nohup(self, ctx: commands.Context):
        try:
            with open("nohup.out", "r") as f:
                await ctx.author.send(f.read()[-1999:])
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @nohup.error
    async def nohup_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("I don't trust you around a linux log file.")

    @commands.command(name='pull')
    @commands.has_any_role(ROLES.TOTALLY_MOD)
    async def pull(self, ctx: commands.Context):
        """Fetches the latest changes from git."""
        try:
            # Run the git pull command
            result = await subprocess.create_subprocess_shell("git pull", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout, stderr = await result.communicate()
            if stdout:
                print(stdout.decode())
            if stderr:
                print(stderr.decode())
            if result.returncode == 0:
                await ctx.send("Successfully pulled the latest changes from git.")
                await ctx.author.send("Git pull output:\n" + stdout.decode())
            else:
                await ctx.send(f"Failed to pull changes: {stderr.decode()}")
        except Exception as e:
            await ctx.send(f"An error occurred while pulling changes: {e}")
    @pull.error
    async def pull_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handles errors for the pull command."""
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("Where are you trying to pull from, the depths of hell?")
        else:
            await ctx.send(f"An unexpected error occurred: {error}")

async def setup(bot: commands.Bot):
    """Sets up the DevCog."""
    await bot.add_cog(DevCog(bot))
    print("DevCog loaded successfully.")