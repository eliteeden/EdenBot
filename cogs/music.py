import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
import subprocess
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

class MusicCog(commands.Cog):
    load_dotenv()
    
    def __init__(self, bot):
        self.bot = bot
        self.GENIUS_API_TOKEN = os.environ.get("GENIUS_API_TOKEN")
        self.queue = []
        self.skip_votes = set()
        self.skip_threshold = 1
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

        try:
            await ctx.author.voice.channel.connect(timeout=30, self_deaf=True)
            await ctx.send("✅ Connected to the voice channel.")
        except asyncio.TimeoutError:
            await ctx.send("❌ Connection timed out. Discord may be slow or unstable.")
        except asyncio.CancelledError:
            await ctx.send("❌ Connection was cancelled. Try again shortly.")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error: `{str(e)}`")

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
        async with ctx.typing():
            if not ctx.author.voice:
                return await ctx.send("⚠️ You must be in a voice channel.")
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()

            source = None
            title = "Unknown Title"

            if "spotify.com" in link:
                await ctx.send("🎧 Processing Spotify playlist...")
                try:
                    subprocess.run(["spotdl", link, "--output", "downloads"], check=True)
                    downloaded = [f for f in os.listdir("downloads") if f.endswith(".mp3")]
                    if not downloaded:
                        return await ctx.send("❌ No tracks found in playlist.")
                    
                    for file in downloaded:
                        path = os.path.join("downloads", file)
                        track = discord.FFmpegPCMAudio(path)
                        self.add_track(discord.PCMVolumeTransformer(track, volume=1.0))
                    await ctx.send(f"📥 Queued {len(downloaded)} tracks from playlist.")
                except Exception as e:
                    return await ctx.send(f"❌ Error with Spotify playlist: `{str(e)}`")

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

    @commands.command(aliases=["skips"])
    @commands.has_permissions(manage_guild=True)
    async def set_skip_threshold(self, ctx, threshold: int):
        self.skip_threshold = max(1, threshold)
        await ctx.send(f"🔧 Skip threshold set to {self.skip_threshold} votes.")

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            return await ctx.send("📭 The queue is empty.")
        self.queue.append((title, discord.FFmpegPCMAudio(audio_url)))
        msg = "\n".join([f"{i+1}. `{str(track)}`" for i, track in enumerate(self.queue)])
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

    @commands.command(aliases=["ll", "lyrics"])
    async def song(self, ctx, *, query: str):
        """Fetch song lyrics from Genius (format: Song Title - Artist)"""
        try:
            async with ctx.typing():
                if "-" not in query:
                    return await ctx.send("Please use the format: `Song Title - Artist`")

                title, artist = map(str.strip, query.split("-", 1))
                search_query = f"{title} {artist}"

                headers = {"Authorization": f"Bearer {self.GENIUS_API_TOKEN}"}

                async with aiohttp.ClientSession() as session:
                    # Search for the song
                    search_url = f"https://api.genius.com/search?q={search_query}"
                    async with session.get(search_url, headers=headers) as resp:
                        if resp.status != 200:
                            return await ctx.send("Could not search Genius.")
                        data = await resp.json()
                        hits = data["response"]["hits"]
                        if not hits:
                            return await ctx.send("No lyrics found.")
                        song_url = hits[0]["result"]["url"]

                    # Scrape the lyrics
                    async with session.get(song_url) as song_resp:
                        html = await song_resp.text()
                        soup = BeautifulSoup(html, "lxml")
                        containers = soup.find_all(
                            "div", attrs={"data-lyrics-container": "true"}
                        )
                        lyrics_lines = []

                        for tag in containers:
                            for element in tag.stripped_strings:
                                lyrics_lines.append(element)

                        lyrics = "\n".join(lyrics_lines)

                if not lyrics:
                    return await ctx.send("Lyrics not found on the page.")

                # Split lyrics into lines and group into chunks under 1024 characters
                lines = lyrics.split("\n")
                chunks = []
                current_chunk = ""

                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= 1024:
                        current_chunk += line + "\n"
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = line + "\n"

                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Send lyrics in embed chunks
                for i, chunk in enumerate(chunks):
                    embed = discord.Embed(
                        title=(
                            f"{title} - {artist}"
                            if i == 0
                            else f"{title} - {artist} (Part {i+1})"
                        ),
                        description=chunk,
                        color=discord.Color.blurple(),
                    )
                    await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: `{e}`")


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
    print("Music cog has been loaded")
