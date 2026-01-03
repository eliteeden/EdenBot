import discord
from discord.ext import commands

class QuotesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Store settings per guild
        self.settings = {}  # {guild_id: {"channel": channel_id, "threshold": int}}

    def get_settings(self, guild_id):
        return self.settings.get(guild_id, {"channel": None, "threshold": 3})

    async def get_starboard_entry(self, starboard_channel, original_message_id):
        async for msg in starboard_channel.history(limit=200):
            if msg.embeds and msg.embeds[0].footer.text.endswith(str(original_message_id)):
                return msg
        return None

    async def handle_starboard(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        settings = self.get_settings(guild.id)
        starboard_channel_id = settings["channel"]
        threshold = settings["threshold"]

        if not starboard_channel_id:
            return  # QuotesCog not configured

        star_count = sum([r.count for r in message.reactions if str(r.emoji) == "⭐"])
        starboard_channel = guild.get_channel(starboard_channel_id)

        existing_entry = await self.get_starboard_entry(starboard_channel, message.id)

        if star_count >= threshold:
            if existing_entry:
                embed = existing_entry.embeds[0]
                await existing_entry.edit(content=f"⭐ {star_count} | {channel.mention}", embed=embed)
            else:
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.gold()
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
                embed.add_field(name="Jump to message", value=f"[Click here]({message.jump_url})")
                embed.set_footer(text=f"Message ID: {message.id}")

                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)

                await starboard_channel.send(f"⭐ {star_count} | {channel.mention}", embed=embed)
        else:
            if existing_entry:
                await existing_entry.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) == "⭐":
            await self.handle_starboard(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) == "⭐":
            await self.handle_starboard(payload)

    # --- Admin Commands ---
    @commands.command(name="setstarboard", aliases=["setquotes"])
    @commands.has_permissions(manage_guild=True)
    async def set_starboard_channel(self, ctx, channel: discord.TextChannel):
        """Set the starboard channel for this server."""
        settings = self.get_settings(ctx.guild.id)
        settings["channel"] = channel.id
        self.settings[ctx.guild.id] = settings
        await ctx.send(f"✅ QuotesCog channel set to {channel.mention}")

    @commands.command(name="setthreshold", aliases=["setstars"])
    @commands.has_permissions(manage_guild=True)
    async def set_star_threshold(self, ctx, threshold: int):
        """Set the star threshold for this server."""
        if threshold < 1:
            return await ctx.send("❌ Threshold must be at least 1.")
        settings = self.get_settings(ctx.guild.id)
        settings["threshold"] = threshold
        self.settings[ctx.guild.id] = settings
        await ctx.send(f"✅ Star threshold set to {threshold}")

async def setup(bot):
    await bot.add_cog(QuotesCog(bot))
    print("QuotesCog has been loaded")