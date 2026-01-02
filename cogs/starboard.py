import discord
from discord.ext import commands

class QuotesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starboard_channel_id = 123456789012345678  # replace with your starboard channel ID
        self.star_threshold = 3  # number of ⭐ reactions required

    async def get_starboard_entry(self, starboard_channel, original_message_id):
        async for msg in starboard_channel.history(limit=200):
            if msg.embeds and msg.embeds[0].footer.text.endswith(str(original_message_id)):
                return msg
        return None

    async def handle_starboard(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # Count stars
        star_count = sum([r.count for r in message.reactions if str(r.emoji) == "⭐"])
        starboard_channel = guild.get_channel(self.starboard_channel_id)

        existing_entry = await self.get_starboard_entry(starboard_channel, message.id)

        if star_count >= self.star_threshold:
            if existing_entry:
                # Update existing entry
                embed = existing_entry.embeds[0]
                await existing_entry.edit(content=f"⭐ {star_count} | {channel.mention}", embed=embed)
            else:
                # Create new entry
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
                # Remove from starboard if below threshold
                await existing_entry.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) == "⭐":
            await self.handle_starboard(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) == "⭐":
            await self.handle_starboard(payload)

async def setup(bot):
    await bot.add_cog(QuotesCog(bot))
    print("QuotesCog has been loaded")