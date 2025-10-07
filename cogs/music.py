import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import subprocess
import os
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
    async def play(self, ctx, *, link: str):
        if not ctx.author.voice:
            await ctx.send("⚠️ You must be in a voice channel.")
            return

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        # Determine link type
        if "spotify.com" in link:
            await ctx.send("🎧 Processing Spotify link...")
            try:
                subprocess.run(["spotdl", link], check=True)
                # Find the downloaded file
                for file in os.listdir():
                    if file.endswith(".mp3"):
                        audio_file = file
                        break
                else:
                    await ctx.send("❌ Could not find downloaded Spotify track.")
                    return
                source = discord.FFmpegPCMAudio(audio_file)
                ctx.voice_client.play(source)
                await ctx.send(f"▶️ Now playing: {audio_file}")
            except Exception as e:
                await ctx.send(f"❌ Error with Spotify link: `{str(e)}`")
        else:
            await ctx.send("🎧 Processing YouTube link...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'default_search': 'auto'
            }
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    audio_url = info['url']
                    title = info.get('title', 'Unknown Title')
                source = discord.FFmpegPCMAudio(audio_url)
                ctx.voice_client.play(source)
                await ctx.send(f"▶️ Now playing: **{title}**")
            except Exception as e:
                await ctx.send(f"❌ Error with YouTube link: `{str(e)}`")

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
