#!/usr/bin/env python3
"""Typeset the selected Atlantic Tracks artwork and check the encoded YouTube JPG."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'deliverables/extinct-life-step-9'
CACHE = ROOT / '.cache/atlantic-cover'
FONT = CACHE / 'fonts/SpaceGrotesk.ttf'
FONT_SHA = 'acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'
TITLE = 'Why Are These Dinosaur Footprints an Ocean Apart?'
COPY = ('6,000', 'KM APART')
SIZE = (1920, 1080)
BYTE_LIMIT = 2_000_000
RESAMPLE = Image.Resampling.LANCZOS


def sha(path: Path) -> str:
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def bold(path: Path, size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size)
    font.set_variation_by_axes([700])
    return font


def render(art: Path, font: Path):
    assert sha(font) == FONT_SHA, 'Use the checksum-pinned Space Grotesk font.'
    with Image.open(art) as source:
        oriented = ImageOps.exif_transpose(source)
        original = oriented.size
        assert abs(original[0] / original[1] - 16 / 9) < .025, 'Artwork must already be near 16:9.'
        profile = oriented.info.get('icc_profile')
        rgb = oriented.convert('RGB')
        if profile:
            rgb = ImageCms.profileToProfile(rgb, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                            ImageCms.createProfile('sRGB'), outputMode='RGB')
        plate = ImageOps.fit(rgb, SIZE, RESAMPLE)
    w, h = SIZE
    # Only the headline lane is graded. Both fossil silhouettes remain unpainted.
    lane = Image.new('L', (1, h))
    lane.putdata([round(42 * (1 - y / 285) ** 2) if y < 285 else 0 for y in range(h)])
    plate = Image.composite(Image.new('RGB', SIZE, (3, 15, 28)), plate, lane.resize(SIZE))
    plate = plate.filter(ImageFilter.UnsharpMask(radius=.85, percent=22, threshold=5))
    fs = (bold(font, 184), bold(font, 154))
    gap = 34
    width = sum(f.getlength(s) for f, s in zip(fs, COPY, strict=True)) + gap
    x, y = (w - width) / 2, 184
    fills = []
    boxes = []
    stroke = Image.new('L', SIZE)
    for f, text in zip(fs, COPY, strict=True):
        key = Image.new('L', SIZE)
        draw = ImageDraw.Draw(key)
        draw.text((x, y), text, anchor='ls', font=f, fill=255)
        ImageDraw.Draw(stroke).text((x, y), text, anchor='ls', font=f, fill=250, stroke_width=4)
        boxes.append(key.getbbox())
        fills.append(key)
        x += f.getlength(text) + gap
    assert all(96 < a < c < w - 96 and 31 < b < d < 225 for a,b,c,d in boxes), boxes
    shade = Image.new('L', SIZE)
    shade.paste(stroke, (0, 11))
    shade = shade.filter(ImageFilter.GaussianBlur(10)).point(lambda v: round(v * .68))
    composite = Image.composite(Image.new('RGB', SIZE, (0, 9, 16)), plate, shade)
    composite = Image.composite(Image.new('RGB', SIZE, (8, 22, 34)), composite, stroke)
    for rgb, mask in zip(((255, 248, 226), (255, 210, 110)), fills, strict=True):
        composite.paste(rgb, (0, 0, w, h), mask)
    return composite, plate, fills, boxes, original


def jpeg(image: Image.Image, target: Path):
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    for q in range(96, 84, -1):
        f = io.BytesIO()
        image.save(f, format='JPEG', quality=q, subsampling=0, optimize=True, icc_profile=icc)
        if f.tell() < BYTE_LIMIT:
            target.write_bytes(f.getvalue())
            return q
    raise ValueError('Thumbnail JPEG exceeds 2 MB.')


def luma(rgb):
    def linear(z):
        z /= 255
        return z / 12.92 if z <= .04045 else ((z + .055) / 1.055) ** 2.4
    return sum(w * linear(x) for w, x in zip((.2126, .7152, .0722), rgb, strict=True))


def audit(target: Path, plate: Image.Image, fills, qa: Path):
    with Image.open(target) as image:
        assert image.format == 'JPEG' and image.size == SIZE and image.mode == 'RGB'
        assert target.stat().st_size < BYTE_LIMIT and image.info.get('icc_profile')
        image.load()
    records = {}
    for w in (480, 320, 176, 120):
        size = (w, round(w * 9 / 16))
        tile = image.resize(size, RESAMPLE)
        base = plate.resize(size, RESAMPLE)
        stats = []
        for mask in fills:
            pixels = mask.resize(size, RESAMPLE)
            ctr = [(luma(a)+.05)/(luma(b)+.05) for a,b,m in
                   zip(tile.getdata(), base.getdata(), pixels.getdata(), strict=True) if m >= 215]
            assert len(ctr) > 4, (w,len(ctr))
            ratio = round(median(ctr), 2)
            assert ratio >= 5.5, (w,ratio)
            bounds = pixels.point(lambda v: 255 if v >= 160 else 0).getbbox()
            stats.append({'median_core_contrast': ratio, 'ink_height_px': bounds[3]-bounds[1]})
        # A feed runtime badge is checked in these QA images only.
        d = ImageDraw.Draw(tile)
        f = ImageFont.load_default(size=max(8, round(w*.035)))
        badge = '7:25'
        b_w = round(d.textlength(badge, font=f)) + 8
        b_h = max(14, round(w*.054))
        x,y = size[0] - b_w - 4, size[1] - b_h - 4
        d.rounded_rectangle((x,y,x+b_w,y+b_h), radius=3, fill=(9,12,14))
        d.text((x+b_w/2,y+b_h/2),badge,font=f,fill='white',anchor='mm')
        tile.save(qa / f'feed-{w}.png')
        records[str(w)] = {'size': list(size), 'headline_spans': stats}
    return records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--art', type=Path, default=OUT/'Atlantic-Tracks-Selected-Art.png')
    p.add_argument('--font', type=Path, default=FONT)
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--qa', type=Path, default=CACHE/'qa')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    a.qa.mkdir(parents=True, exist_ok=True)
    finished, base, masks, ink, original = render(a.art, a.font)
    target = a.out/'Atlantic-Tracks-YouTube-Thumbnail.jpg'
    q = jpeg(finished, target)
    tests = audit(target, base, masks, a.qa)
    (a.out/'Atlantic-Tracks-YouTube-Title.txt').write_text(TITLE+'\n', encoding='utf-8')
    receipt = {
        'for_film': 'Atlantic Tracks — Cinema Edition (07:25.667)',
        'youtube_title': TITLE, 'thumbnail_copy': ' '.join(COPY),
        'copy_context': 'Approximate present-day separation of the Sousa and Koum regions; not a dinosaur route.',
        'art': 'Original generated illustration with distinct footprint impressions; not specimen or site photography.',
        'art_px': list(original), 'art_sha256': sha(a.art), 'font_sha256': sha(a.font),
        'image': {'name': target.name, 'bytes': target.stat().st_size, 'sha256': sha(target),
                  'px': list(SIZE), 'jpeg_quality': q, 'profile': 'sRGB', 'text_ink_boxes': ink},
        'encoded_feed_qa': tests, 'not_published_or_audience_tested': True,
    }
    (a.qa/'cover-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
