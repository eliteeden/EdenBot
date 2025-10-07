import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import subprocess
import os
import asyncio

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.skip_votes = set()
        self.skip_threshold = 3
        self.current_track = None

    def track_finished(self, error):
        self.skip_votes.clear()
        if self.queue:
            self.current_track = self.queue.pop(0)
            self.voice_client.play(self.current_track, after=self.track_finished)

    def add_track(self, track: discord.AudioSource):
        self.queue.append(track)
        if not self.voice_client.is_playing():
            self.current_track = self.queue.pop(0)
            self.voice_client.play(self.current_track, after=self.track_finished)

    @property
    def voice_client(self):
        # Get the first connected voice client
        for vc in self.bot.voice_clients:
            if vc.is_connected():
                return vc
        return None

    @commands.command()
    async def connect(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("⚠️ You are not connected to a voice channel.")
        await ctx.author.voice.channel.connect()
        await ctx.send("✅ Connected to the voice channel.")

    @commands.command()
    async def disconnect(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("⚠️ I'm not connected to any voice channel.")
        await ctx.voice_client.disconnect()
        self.queue.clear()
        self.skip_votes.clear()
        await ctx.send("👋 Disconnected.")

    @commands.command()
    async def play(self, ctx, *, link: str):
        if not ctx.author.voice:
            return await ctx.send("⚠️ You must be in a voice channel.")
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        source = None
        title = "Unknown Title"

        if "spotify.com" in link:
            await ctx.send("🎧 Processing Spotify link...")
            try:
                subprocess.run(["spotdl", link], check=True)
                for file in os.listdir():
                    if file.endswith(".mp3"):
                        source = discord.FFmpegPCMAudio(file)
                        title = file
                        break
                else:
                    return await ctx.send("❌ Could not find downloaded Spotify track.")
            except Exception as e:
                return await ctx.send(f"❌ Error with Spotify link: `{str(e)}`")
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
            except Exception as e:
                return await ctx.send(f"❌ Error with YouTube link: `{str(e)}`")

        if source:
            self.add_track(discord.PCMVolumeTransformer(source, volume=1.0))
            await ctx.send(f"▶️ Queued: **{title}**")

    @commands.command()
    async def skip(self, ctx):
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            return await ctx.send("⚠️ Nothing is playing.")

        if ctx.author.id in self.skip_votes:
            return await ctx.send("🗳️ You already voted to skip.")

        self.skip_votes.add(ctx.author.id)
        votes = len(self.skip_votes)

        if votes >= self.skip_threshold:
            vc.stop()
            await ctx.send("⏭️ Track skipped by vote!")
        else:
            await ctx.send(f"🗳️ Skip vote added ({votes}/{self.skip_threshold}).")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def set_skip_threshold(self, ctx, threshold: int):
        self.skip_threshold = max(1, threshold)
        await ctx.send(f"🔧 Skip threshold set to {self.skip_threshold} votes.")

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            return await ctx.send("📭 The queue is empty.")
        msg = "\n".join([f"{i+1}. {str(track)}" for i, track in enumerate(self.queue)])
        await ctx.send(f"📜 Current Queue:\n{msg}")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused playback.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed playback.")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
