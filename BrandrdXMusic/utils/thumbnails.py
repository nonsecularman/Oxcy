import os
import re
import random

import aiofiles
import aiohttp

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)

from unidecode import unidecode
from py_yt import VideosSearch

from BrandrdXMusic import app
from config import YOUTUBE_IMG_URL


# ================== Utils ==================

def changeImageSize(maxWidth, maxHeight, image):
    ratio = min(maxWidth / image.size[0], maxHeight / image.size[1])
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    return image.resize(new_size, Image.LANCZOS)


def clear(text, limit=60):
    words = text.split()
    out = ""
    for w in words:
        if len(out) + len(w) <= limit:
            out += " " + w
    return out.strip()


# ================== Main ==================

async def get_thumb(videoid):
    cache_file = f"cache/{videoid}.png"
    temp_file = f"cache/temp_{videoid}.png"

    if os.path.isfile(cache_file):
        return cache_file

    try:
        search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = (await search.next())["result"][0]

        title = clear(re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title())
        duration = data.get("duration", "Unknown")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "Unknown Channel")
        thumb_url = data["thumbnails"][0]["url"].split("?")[0]

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(temp_file, "wb") as f:
                    await f.write(await resp.read())

        # Open image
        youtube = Image.open(temp_file).convert("RGB")
        image = changeImageSize(1280, 720, youtube)

        # Blur background
        background = image.filter(ImageFilter.GaussianBlur(8))
        background = ImageEnhance.Brightness(background).enhance(0.85)
        background = ImageEnhance.Contrast(background).enhance(1.2)

        # Neon border
        colors = ["cyan", "magenta", "blue", "red", "green", "yellow"]
        background = ImageOps.expand(background, border=6, fill=random.choice(colors))
        background = changeImageSize(1280, 720, background)

        draw = ImageDraw.Draw(background)

        # Fonts
        font_title = ImageFont.truetype("BrandrdXMusic/assets/font.ttf", 42)
        font_small = ImageFont.truetype("BrandrdXMusic/assets/font2.ttf", 28)

        # Text
        draw.text((30, 30), title, fill="white", font=font_title)
        draw.text((30, 90), f"{channel} • {views}", fill="white", font=font_small)
        draw.text((1100, 20), unidecode(app.name), fill="white", font=font_small)
        draw.text((30, 650), duration, fill="white", font=font_small)

        # Save
        os.remove(temp_file)
        background.save(cache_file, "PNG")

        return cache_file

    except Exception as e:
        print(f"[THUMB ERROR] {e}")
        return YOUTUBE_IMG_URL
