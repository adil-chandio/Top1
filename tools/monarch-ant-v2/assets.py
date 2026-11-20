from pathlib import Path
import os
from PIL import Image, ImageOps

C=Path(os.environ.get('MONARCH_V2_CACHE','.cache/monarch-ant-v2'))/'assets'
for name,w,h in [('fine-quartz',1024,1024),('fern-light',1024,576),('chitin-micro',768,768)]:
    with Image.open(C/(name+'.png')) as im:
        im=ImageOps.fit(im.convert('RGBA'),(w,h),Image.Resampling.LANCZOS)
        (C/(name+'.rgba')).write_bytes(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())
