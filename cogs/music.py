from curses.panel import bottom_panel
import discord
from discord.ext import commands
import asyncio
from youtube_dl import YoutubeDL

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
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"Joined {channel.name}!")
        else:
            await ctx.send("You need to be in a voice channel first!")

    # Leave voice channel command
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from the voice channel!")
        else:
            await ctx.send("I'm not in a voice channel!")

    # Play audio command
    @commands.command()
    async def play(self, ctx, url: str):
        if not ctx.voice_client:
            await ctx.send("I'm not connected to a voice channel!")
            return

        # Ensure ffmpeg is installed and in PATH
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        # Use youtube_dl to extract audio
        
        ydl_opts = {'format': 'bestaudio/best', 'noplaylist': 'True'}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']

        # Play the audio
        ctx.voice_client.stop()  # Stop any currently playing audio
        ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))
        await ctx.send(f"Now playing: {info['title']}")

# Run the bot
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("[MusicCog] loaded successfully")