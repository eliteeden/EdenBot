import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "verify_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    async def cog_load(self):
        """Automatically reload verification setup when cog is loaded"""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.config:
                continue

            channel = guild.get_channel(self.config[guild_id]["channel_id"])
            role = guild.get_role(self.config[guild_id]["role_id"])

            if not channel or not role:
                continue

            try:
                # Send verification message with reaction
                msg = await channel.send("React with ✅ to verify yourself!")
                await msg.add_reaction("✅")
                print(f"Verification message reloaded in {guild.name}")
            except Exception as e:
                print(f"Failed to reload verification in {guild.name}: {e}")

    @commands.command(name="verifysetup", aliases=["verifyy"])
    @commands.has_permissions(manage_channels=True)
    async def verifysetup(self, ctx, channel: discord.TextChannel, role: discord.Role):
        """
        Setup verification system.
        Usage: !verifysetup #channel @role
        """

        # Save config for persistence
        self.config[str(ctx.guild.id)] = {
            "channel_id": channel.id,
            "role_id": role.id
        }
        save_config(self.config)

        # Step 1: Lock all channels to only verified role
        for ch in ctx.guild.channels:
            if ch == channel:
                continue

            # Hide from @everyone
            overwrite = ch.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)

            # Allow verified role
            overwrite_verified = ch.overwrites_for(role)
            overwrite_verified.view_channel = True
            await ch.set_permissions(role, overwrite=overwrite_verified)

        # Step 2: Send verification message with reaction
        msg = await channel.send("React with ✅ to verify yourself!")
        await msg.add_reaction("✅")

        await ctx.send("✅ Verification system setup complete!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Grant role when user reacts with ✅"""
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        guild_id = str(guild.id)
        if guild_id not in self.config:
            return

        role = guild.get_role(self.config[guild_id]["role_id"])
        if not role:
            return

        # Ensure it's the right channel and emoji
        if payload.channel_id != self.config[guild_id]["channel_id"]:
            return
        if str(payload.emoji) != "✅":
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        try:
            await member.add_roles(role)
            print(f"{member} verified in {guild.name}")
        except discord.Forbidden:
            print(f"❌ Missing permissions to assign role in {guild.name}")

# --- Cog Setup Function ---
async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
    print("VerificationCog has been loaded successfully")