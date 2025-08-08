import requests
import os
from PIL import Image, ImageFont, ImageOps, ImageDraw
from io import BytesIO

class RANKCARD():
    def rank_card(
        self,
        username,
        avatar,
        level,
        rank,
        current_xp,
        next_level_xp,
        custom_background,
        xp_color,
        formatted_current_xp,
        formatted_next_level_xp,
        background_opacity=130  # 👈 New parameter
    ):
        # Convert hex to RGB
        bg_rgb = tuple(int(custom_background[i:i+2], 16) for i in (1, 3, 5))

        # Create transparent canvas
        img = Image.new('RGBA', (934, 282), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw semi-transparent background
        draw.rectangle(
            [(0, 0), (934, 282)],
            fill=bg_rgb + (background_opacity,)
        )

        # Load avatar
        response = requests.get(avatar)
        img_avatar = Image.open(BytesIO(response.content)).convert("RGBA")

        # Create circular mask
        bigsize = (img_avatar.size[0] * 3, img_avatar.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(img_avatar.size)
        img_avatar.putalpha(mask)

        # Resize and paste avatar
        img_avatar = img_avatar.resize((170, 170))
        img.paste(img_avatar, (50, 50), img_avatar)

        # Draw progress bar
        draw = self.drawProgressBar(draw, 260, 180, 575, 40, current_xp / next_level_xp if next_level_xp > 0 else 0, bg="#000000", fg=xp_color)

        # Load fonts
        font = ImageFont.truetype("arial/arialceb.ttf", size=50)
        font2 = ImageFont.truetype("arial/ArialCE.ttf", size=25)

        # Add text
        draw.text((260, 100), username, fill=(255, 255, 255), font=font)
        draw.text((650, 100), f"{formatted_current_xp}/{formatted_next_level_xp} XP", fill=(255, 255, 255), font=font2)
        draw.text((650, 50), f"LEVEL {level}", fill=xp_color, font=font)
        draw.text((260, 50), f"RANK #{rank}", fill=(255, 255, 255), font=font2)

        # Add gray border
        img = ImageOps.expand(img, border=5, fill='gray')

        # Save image
        output_path = f"{os.getcwd()}/rankcards2.png"
        img.save(output_path)
        return output_path

    def drawProgressBar(self, d, x, y, w, h, progress, bg="black", fg="red"):
        # Draw background
        d.ellipse((x + w, y, x + h + w, y + h), fill=bg)
        d.ellipse((x, y, x + h, y + h), fill=bg)
        d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=bg)

        # Draw progress
        w *= progress
        d.ellipse((x + w, y, x + h + w, y + h), fill=fg)
        d.ellipse((x, y, x + h, y + h), fill=fg)
        d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=fg)

        return d