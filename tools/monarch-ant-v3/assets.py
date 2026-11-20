"""Pack the two generated image inputs and V2 cuticle into GL textures."""
import os
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(os.environ.get('MONARCH_V3_CACHE', '.cache/monarch-ant-v3'))
V2 = Path('deliverables/monarch-cam-step-4-v2/source-assets')


def pack():
    p = ROOT / 'assets'
    for src, filename, size, blur in [
        (p/'dune-quartz.png', 'quartz', (1024, 1024), 0),
        (p/'forest-bokeh.png', 'canopy', (1024, 576), 13.4),
        (V2/'chitin-micro.png', 'cuticle', (768, 768), 0),
    ]:
        with Image.open(src) as im:
            a = ImageOps.fit(im.convert('RGBA'), size, Image.Resampling.LANCZOS)
            if blur:
                a = a.filter(ImageFilter.GaussianBlur(blur))
            (p/f'{filename}.rgba').write_bytes(a.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())


if __name__ == '__main__':
    pack()
