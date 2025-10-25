
import discord
from discord.ext import commands
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
import aiohttp
import io
import math
import numpy as np
import cv2

DEFAULT_FONT_PATH = "arial/ARIAL.TTF"

def ensure_font(size=40):
    try:
        return ImageFont.truetype(DEFAULT_FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

async def fetch_image_bytes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()

def open_image_from_bytes(bts):
    return Image.open(io.BytesIO(bts)).convert("RGBA")

def to_bytes_io(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf

class ImageCog(commands.Cog, name="esmImage"):
    def __init__(self, bot):
        self.bot = bot

    async def _get_attachment_or_fail(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Please attach an image.")
            return None
        url = ctx.message.attachments[0].url
        try:
            b = await fetch_image_bytes(url)
            return open_image_from_bytes(b)
        except Exception:
            await ctx.send("Failed to download or open the image.")
            return None

    # Image transforms
    @commands.command()
    async def invert(self, ctx):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        inv = ImageOps.invert(img.convert("RGB")).convert("RGBA")
        await ctx.send(file=discord.File(to_bytes_io(inv), "inverted.png"))

    @commands.command()
    async def grayscale(self, ctx):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        g = img.convert("L").convert("RGBA")
        await ctx.send(file=discord.File(to_bytes_io(g), "grayscale.png"))

    @commands.command()
    async def blur(self, ctx, radius: float = 5.0):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        b = img.filter(ImageFilter.GaussianBlur(radius))
        await ctx.send(file=discord.File(to_bytes_io(b), "blurred.png"))

    @commands.command()
    async def rotate(self, ctx, degrees: float = 90.0):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        r = img.rotate(-degrees, expand=True)
        await ctx.send(file=discord.File(to_bytes_io(r), "rotated.png"))

    @commands.command()
    async def resize(self, ctx, width: int, height: int):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        r = img.resize((max(1, width), max(1, height)), Image.LANCZOS)
        await ctx.send(file=discord.File(to_bytes_io(r), "resized.png"))

    @commands.command()
    async def border(self, ctx, size: int = 10, color: str = "#000000"):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        bordered = ImageOps.expand(img, border=size, fill=color)
        await ctx.send(file=discord.File(to_bytes_io(bordered), "bordered.png"))

    @commands.command()
    async def pixelate(self, ctx, scale: int = 10):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        w, h = img.size
        small = img.resize((max(1, w//scale), max(1, h//scale)), resample=Image.NEAREST)
        pix = small.resize((w, h), Image.NEAREST)
        await ctx.send(file=discord.File(to_bytes_io(pix), "pixelated.png"))

    @commands.command()
    async def deepfry(self, ctx, contrast: float = 2.0, color: float = 3.0, sharpen: float = 2.0):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        im = img.convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(contrast)
        im = ImageEnhance.Color(im).enhance(color)
        im = ImageEnhance.Sharpness(im).enhance(sharpen)
        # add heavy JPEG artifacts via OpenCV encode/decode
        arr = cv2.imencode('.jpg', cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), 40])[1].tobytes()
        im = Image.open(io.BytesIO(arr)).convert("RGBA")
        await ctx.send(file=discord.File(to_bytes_io(im), "deepfried.png"))

    # Overlay / compositing
    @commands.command()
    async def watermark(self, ctx, *, text: str = "Watermark"):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        base = img.copy()
        w, h = base.size
        txt = Image.new('RGBA', base.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        font = ensure_font(max(24, w//20))
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]  # text width
        th = bbox[3] - bbox[1]  # text height
        draw.text((w-tw-10, h-th-10), text, font=font, fill=(255,255,255,120))
        composed = Image.alpha_composite(base, txt)
        await ctx.send(file=discord.File(to_bytes_io(composed), "watermarked.png"))

    @commands.command()
    async def caption(self, ctx, *, text: str):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        w, h = img.size
        font = ensure_font(max(20, w//15))
        # create new image with space for top and bottom text if needed
        pad = int(h * 0.15)
        new_h = h + pad
        new_img = Image.new("RGBA", (w, new_h), (0,0,0,255))
        new_img.paste(img, (0, pad//2))
        draw = ImageDraw.Draw(new_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((w-tw)/2, 5), text, font=font, fill=(255,255,255,255))
        await ctx.send(file=discord.File(to_bytes_io(new_img), "captioned.png"))

    @commands.command()
    async def overlay(self, ctx, url: str):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        try:
            b = await fetch_image_bytes(url)
            overlay = open_image_from_bytes(b).convert("RGBA")
        except Exception:
            await ctx.send("Failed to fetch overlay image.")
            return
        overlay = overlay.resize(img.size, Image.LANCZOS)
        composed = Image.alpha_composite(img, overlay)
        await ctx.send(file=discord.File(to_bytes_io(composed), "overlayed.png"))

    # Meme / style effects
    @commands.command(aliases=["triggered"])
    async def triggered_cmd(self, ctx):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        # red tint + shake crop + add triggered banner
        w, h = img.size
        # red boost
        arr = np.array(img.convert("RGB")).astype(np.int16)
        arr[:,:,0] = np.clip(arr[:,:,0] * 1.6, 0, 255)
        arr = arr.astype('uint8')
        im = Image.fromarray(arr).convert("RGBA")
        # shake frames -> single GIF-like style (we return a single image simulated by offset)
        off = Image.new("RGBA", (w, h), (0,0,0,0))
        off.paste(im, (int(w*0.02), 0))
        off2 = Image.new("RGBA", (w, h), (0,0,0,0))
        off2.paste(im, (int(-w*0.02), 0))
        base = Image.alpha_composite(off, off2)
        # banner
        draw = ImageDraw.Draw(base)
        font = ensure_font(max(24, w//10))
        banner_h = int(h * 0.12)
        draw.rectangle(((0, h-banner_h), (w, h)), fill=(255,0,0,255))
        bbox = draw.textbbox((0, 0), "TRIGGERED", font=font)
        tw = bbox[2] - bbox[0]  # text width
        th = bbox[3] - bbox[1]  # text height

        draw.text(
            ((w - tw) // 2, h - banner_h // 2 - th // 2),
            "TRIGGERED",
            font=font,
            fill=(255, 255, 255, 255)
        )
        await ctx.send(file=discord.File(to_bytes_io(base), "triggered.png"))

    @commands.command()
    async def petpet(self, ctx):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        # simple petpet: small repeated scale/rotate frames -> produce a GIF composed from frames
        try:
            frames = []
            w,h = img.size
            base = img.copy().convert("RGBA")
            for scale in [0.95, 0.92, 0.98, 1.0]:
                f = base.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
                frame = Image.new("RGBA", (w, h), (0,0,0,0))
                frame.paste(f, ((w - f.width)//2, (h - f.height)//2), f)
                frames.append(frame.convert("P", palette=Image.ADAPTIVE))
            buf = io.BytesIO()
            frames[0].save(buf, format='GIF', save_all=True, append_images=frames[1:], loop=0, duration=60, disposal=2)
            buf.seek(0)
            await ctx.send(file=discord.File(buf, "petpet.gif"))
        except Exception:
            await ctx.send("Failed to create petpet animation.")

    @commands.command()
    async def cursed(self, ctx):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        w,h = img.size
        # apply posterize, color shift, and rotate skew
        im = img.convert("RGB")
        im = ImageOps.posterize(im, bits=3)
        arr = np.array(im).astype(np.int16)
        arr = np.clip(arr + np.array([20, -50, 20]), 0, 255).astype('uint8')
        im = Image.fromarray(arr).convert("RGBA")
        im = im.rotate(3, expand=True).resize((w,h))
        # add vignette
        vignette = Image.new("L", (w,h))
        for x in range(w):
            for y in range(h):
                dx = (x - w/2) / (w/2)
                dy = (y - h/2) / (h/2)
                d = math.sqrt(dx*dx + dy*dy)
                vignette.putpixel((x,y), int(255 * (1 - min(1, d))))
        im.putalpha(vignette)
        await ctx.send(file=discord.File(to_bytes_io(im), "cursed.png"))

    @commands.command()
    async def comic(self, ctx, lines: int = 3):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        w,h = img.size
        # halftone via opencv
        gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,9,9)
        color = cv2.bilateralFilter(np.array(img.convert("RGB")), 9, 300, 300)
        combo = cv2.bitwise_and(color, color, mask=edges)
        out = Image.fromarray(combo).convert("RGBA")
        await ctx.send(file=discord.File(to_bytes_io(out), "comic.png"))

    @commands.command()
    async def ascii(self, ctx, cols: int = 80):
        img = await self._get_attachment_or_fail(ctx)
        if not img: return
        # convert to grayscale and map to chars
        gray = img.convert("L")
        W, H = gray.size
        scale = W / float(cols)
        rows = int(H/scale/2)
        small = gray.resize((cols, max(1, rows)))
        pixels = np.array(small)
        chars = "@%#*+=-:. "
        lines = []
        for row in pixels:
            line = "".join(chars[int(pixel/255*(len(chars)-1))] for pixel in row)
            lines.append(line)
        text = "\n".join(lines)
        if len(text) > 1990:
            await ctx.send("ASCII output too large.")
            return
        await ctx.send(f"```\n{text}\n```")

async def setup(bot):
    await bot.add_cog(ImageCog(bot))
    print("ImageCog loaded successfully")