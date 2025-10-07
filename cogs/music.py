import discord
from discord.ext import commands
import asyncio
from typing import cast
from yt_dlp import YoutubeDL

# Intents setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True

# Bot setup
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Join voice channel command
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"🎶 Joined `{channel.name}`!")
        else:
            await ctx.send("⚠️ You need to be in a voice channel first!")

    # Leave voice channel command
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Disconnected from the voice channel!")
        else:
            await ctx.send("⚠️ I'm not in a voice channel!")

    # Play audio command
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play(self, ctx, url: str):
        if not ctx.author.voice:
            await ctx.send("⚠️ You must be in a voice channel to use this command.")
            return

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        ydl_opts = cast(dict[str, object], {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
            'quiet': True,
            'default_search': 'auto'
        })

        # Assume audio_url and title are already extracted above

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        try:
            ctx.voice_client.stop()
            ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))
            await ctx.send(f"▶️ Now playing: **{title}**")
            await asyncio.sleep(2)
            if not ctx.voice_client.is_playing():
                await ctx.send("⚠️ Something went wrong—no audio is playing.")
        except Exception as e:
            await ctx.send(f"❌ Error playing audio: `{str(e)}`")

# Run the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("[MusicCog] loaded successfully")
