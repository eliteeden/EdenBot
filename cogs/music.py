import discord
from discord.ext import commands
from typing import Optional
import asyncio

class CustomVoiceClient(discord.VoiceClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = []

    def track_finished(self, error):
        self.queue.pop(0)
        if self.queue:
            self.play(self.queue[0], after=self.track_finished)

    def add_track(self, track: discord.AudioSource):
        self.queue.append(track)
        if len(self.queue) == 1:
            self.play(track, after=self.track_finished)

    def skip_track(self):
        if self.is_playing():
            self.stop()
        elif self.queue:
            self.queue.pop(0)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def connect(self, ctx: commands.Context):
        if ctx.author.voice is None:
            return await ctx.send("⚠️ You are not connected to a voice channel.")
        await ctx.author.voice.channel.connect(cls=CustomVoiceClient)
        await ctx.send("✅ Connected to the voice channel.")

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        if ctx.voice_client is None:
            return await ctx.send("⚠️ I'm not connected to any voice channel.")
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected.")

    @commands.command()
    async def play(self, ctx: commands.Context, file: str):
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect(cls=CustomVoiceClient)

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f"music/{file}.mp3"))
        ctx.voice_client.add_track(source)
        await ctx.send(f"🎵 Added `{file}` to the queue.")

    @commands.command()
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused playback.")

    @commands.command()
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed playback.")

    @commands.command()
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client:
            ctx.voice_client.skip_track()
            await ctx.send("⏭️ Skipped track.")

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"🔊 Volume set to {volume}%.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
