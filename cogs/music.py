import discord
from discord.ext import commands
import asyncio
from yt_dlp import YoutubeDL

from typing import Dict, cast



class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
                
        self.ydl_opts: Dict[str, object] = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'auto'
        }

        self.ffmpeg_options: Dict[str, str] = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
            

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def join(self, ctx):
        print("[join] Command triggered")
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            print(f"[join] Author is in channel: {channel.name}")
            if ctx.voice_client and ctx.voice_client.is_connected():
                print("[join] Bot is already connected")
                await ctx.send(f"✅ Already connected to `{channel.name}`.")
            else:
                try:
                    await channel.connect()
                    await asyncio.sleep(1)
                    print("[join] Bot connected successfully")
                    await ctx.send(f"🎶 Joined `{channel.name}`!")
                except Exception as e:
                    print(f"[join] Connection error: {e}")
                    await ctx.send(f"❌ Failed to join: `{str(e)}`")
        else:
            print("[join] Author not in voice channel")
            await ctx.send("⚠️ You need to be in a voice channel first!")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leave(self, ctx):
        print("[leave] Command triggered")
        if ctx.voice_client:
            try:
                await ctx.voice_client.disconnect()
                print("[leave] Bot disconnected successfully")
                await ctx.send("👋 Disconnected from the voice channel!")
            except Exception as e:
                print(f"[leave] Disconnect error: {e}")
                await ctx.send(f"❌ Failed to disconnect: `{str(e)}`")
        else:
            print("[leave] Bot not in voice channel")
            await ctx.send("⚠️ I'm not in a voice channel!")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play(self, ctx, *, url: str):
        print("[play] Command triggered")
        if not ctx.author.voice:
            print("[play] Author not in voice channel")
            await ctx.send("⚠️ You must be in a voice channel to use this command.")
            return

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            try:
                print("[play] Bot not connected, attempting to connect")
                await ctx.author.voice.channel.connect()
                await asyncio.sleep(1)
                print("[play] Bot connected successfully")
            except Exception as e:
                print(f"[play] Connection error: {e}")
                await ctx.send(f"❌ Failed to connect: `{str(e)}`")
                return

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        ydl_opts = cast(dict[str, object], {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'auto',
            'extract_flat': False
        })

        try:
            print(f"[play] Extracting audio from URL: {url}")
            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
                title = info.get('title', 'Unknown Title')
                print(f"[play] Extracted audio: {title}")
        except Exception as e:
            print(f"[play] Extraction error: {e}")
            await ctx.send(f"❌ Error extracting audio: `{str(e)}`")
            return

        try:
            print("[play] Attempting to play audio")
            ctx.voice_client.stop()
            ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options))
            await ctx.send(f"▶️ Now playing: **{title}**")
            await asyncio.sleep(2)
            if not ctx.voice_client.is_playing():
                print("[play] Playback failed or silent")
                await ctx.send("⚠️ Something went wrong—no audio is playing.")
            else:
                print("[play] Playback started successfully")
        except Exception as e:
            print(f"[play] Playback error: {e}")
            await ctx.send(f"❌ Error playing audio: `{str(e)}`")

# Setup function
async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("[MusicCog] Cog loaded")
