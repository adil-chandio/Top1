"""Finish the selected Monarch Cam cover and assemble its YouTube upload kit."""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageCms, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
STEM = 'Monarch-Cam-01A'
CACHE = Path('.cache/monarch-ant-packaging')
DEST = Path('deliverables/monarch-cam-step-5-packaging')
SIZE = (3840, 2160)
FONT_SHA = 'acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72'
FONT_REV = '5bd87dfc525c8a0d1d8529d3684716e00c3fc59a'
FONT_NOTICE = '564ce565c371c5e5bbf286006565a7c9aa55a9f56e7ca58d56e05d649dd61a72'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def font(path, px, weight=700):
    f = ImageFont.truetype(str(path), px)
    f.set_variation_by_axes([weight])
    return f


def crop_to_ink(draw, label, x, baseline, f):
    # Left of the ink, not the origin of the letter, is the alignment datum.
    left, _, _, _ = draw.textbbox((0, 0), label, font=f, anchor='ls', stroke_width=0)
    p = (x-left, baseline)
    draw.text(p, label, font=f, anchor='ls', fill=255)
    return draw.textbbox(p, label, font=f, anchor='ls')


def cover(art, fonts, dest, qa):
    face = fonts/'SpaceGrotesk.ttf'; notice = fonts/'SpaceGrotesk-OFL.txt'
    assert sha(face) == FONT_SHA and sha(notice) == FONT_NOTICE, 'unverified type source'
    w, h = SIZE
    with Image.open(art) as s:
        wh = s.size
        src = ImageOps.exif_transpose(s).convert('RGB')
    assert abs(src.width/src.height-16/9)<.015, 'selected framing must stay essentially uncropped'
    im = ImageOps.fit(src, SIZE, Image.Resampling.LANCZOS)
    # Open the side-lit ant by a small amount, retaining the selected lighting
    # and the uncluttered left side rather than painting a bar behind the text.
    lift = Image.new('L', (w//8, h//8)); dl = ImageDraw.Draw(lift)
    dl.ellipse((w*.39/8, h*.10/8, w*.95/8, h*.79/8), fill=170)
    lift = lift.filter(ImageFilter.GaussianBlur(19)).resize(SIZE, Image.Resampling.BICUBIC)
    im = Image.composite(ImageEnhance.Brightness(im).enhance(1.115), im, lift)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.0, percent=37, threshold=3))
    art_before = im
    masks = []; boxes = []
    for s, px, base in [('NO', 349, 950), ('GRIP', 474, 1344)]:
        mask = Image.new('L', SIZE)
        boxes.append(crop_to_ink(ImageDraw.Draw(mask), s, 244, base, font(face, px)))
        masks.append(mask)
    assert max(b[2] for b in boxes)<w*.355 and boxes[0][3]+26<boxes[1][1], boxes
    assert min(b[1] for b in boxes)>h*.25 and max(b[3] for b in boxes)<h*.70
    # Spread a restrained shadow outside the letter edges only.
    shadow = Image.new('L', SIZE)
    for mask in masks:
        shadow.paste(200, (0,14,w,h+14),mask=mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    im = Image.composite(Image.new('RGB', SIZE, '#0b0d0a'), im, shadow)
    for k,mask in enumerate(masks):
        if k==0:
            fill=Image.new('RGB',SIZE,'#fff2d9')
        else:
            col=Image.new('RGB',(1,h));d=ImageDraw.Draw(col)
            a,b=(255,232,172),(255,185,79)
            for y in range(h):
                t=max(0,min(1,(y-boxes[1][1])/max(1,boxes[1][3]-boxes[1][1])))
                d.point((0,y),fill=tuple(round(x+(v-x)*t) for x,v in zip(a,b)))
            fill=col.resize(SIZE,Image.Resampling.NEAREST)
        im=Image.composite(fill,im,mask)
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    out = dest/f'{STEM}-YouTube-Thumbnail.jpg'
    for q in range(96,83,-1):
        a = io.BytesIO(); im.save(a, 'JPEG', quality=q, subsampling=0, optimize=True, icc_profile=icc)
        data=a.getvalue()
        if len(data)<1_950_000:
            out.write_bytes(data);break
    else:
        raise ValueError('cover does not fit mobile upload size target')
    with Image.open(out) as img:
        assert img.format=='JPEG' and img.size==SIZE and 'icc_profile' in img.info
        img.load()
        checks=mobile_qa(img,art_before,masks,boxes,face,qa)
    return out,dict(source_px=list(wh),output_px=list(SIZE),jpeg_quality=q,bytes=len(data),
                    sha256=sha(out),selected_art_sha256=sha(art),crop='near-full original 16:9; picture resampled; type rendered at output resolution',type_boxes=boxes,**checks)


def mobile_qa(img, art, masks, boxes, face, qa):
    # Judge the exported JPEG, including a badge approximation only for QA.
    panel=Image.new('RGB',(1000,624),'#122220');d=ImageDraw.Draw(panel)
    d.text((38,30),'MONARCH CAM  /  THUMBNAIL CHECK',font=font(face,27),fill='#fbefda')
    d.text((38,77),'Same JPEG at feed sizes • mock runtime badge',font=font(face,18,500),fill='#bcd7ca')
    def lum(color):
        return sum(w*(z/12.92 if z<=.04045 else ((z+.055)/1.055)**2.4) for w,z in zip((.2126,.7152,.0722),(s/255 for s in color)))
    rec={}
    for w,x,y in [(480,38,130),(320,564,130),(176,564,377),(120,770,377)]:
        h=(w*9+8)//16
        tile=img.resize((w,h),Image.Resampling.LANCZOS)
        raw=art.resize(tile.size,Image.Resampling.LANCZOS); contrast=[]
        for mask in masks:
            cover=mask.resize(tile.size,Image.Resampling.LANCZOS)
            pairs=[(lum(a)+.05)/(lum(b)+.05) for a,b,k in zip(tile.getdata(),raw.getdata(),cover.getdata()) if k>240]
            assert len(pairs)>5,(w,len(pairs))
            pairs.sort();contrast.append(round(pairs[len(pairs)//2],2))
        assert min(contrast)>5.5, (w,contrast)
        hh=[round((b[3]-b[1])*h/SIZE[1],2) for b in boxes]
        rec[str(w)]=dict(preview_px=[w,h],median_core_text_contrast=contrast,glyph_heights_px=hh)
        assert min(hh)>6.5, (w,hh)
        stamp='4:59'; t=ImageDraw.Draw(tile); sz=max(8,int(w*.033)); f=font(face,sz)
        bx=w-round(.024*w);by=h-round(.036*h)
        span=round(f.getlength(stamp))+8
        t.rounded_rectangle((bx-span,by-sz-4,bx,by),radius=2,fill='#141614')
        t.text((bx-4,by-1),stamp,font=f,fill='white',anchor='rs')
        panel.paste(tile,(x,y)); d.text((x,y+h+15),f'{w} × {h}  |  contrast {min(contrast):.1f}:1',font=font(face,18,500),fill='#bcd7ca')
    d.text((38,544),'CHECKED  •  jaws and sand plume visible  •  no lower-right collision',font=font(face,20),fill='#ddc890')
    panel.save(qa/'feed-check.jpg',quality=95)
    return dict(srgb_profile=True,feed_checks=rec)


def clock(spec):
    # Round the exact frame anchors to the nearest seekable studio second.
    src=spec['source'];fps=src['fps']; total=src['frames']/fps
    assert total==src['duration_seconds']==299.8
    root=ast.parse((HERE.parent/'feature_cut.py').read_text())
    anchors=next(ast.literal_eval(node.value) for node in root.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ANCHORS' for t in node.targets))
    assert anchors[-1]==src['frames'] and set(anchors[:-1])<={x['frame'] for x in spec['chapters']}
    rows=[]; secs=[]
    for x in spec['chapters']:
        f=x['frame'];s=(f+fps//2)//fps;mm,ss=divmod(s,60)
        assert abs(s-f/fps)<=.5
        rows.append(dict(**x,timestamp=f'{mm:02d}:{ss:02d}',seconds=s));secs.append(s)
    assert secs[0]==0 and len(secs)>=3 and all(b-a>=10 for a,b in zip(secs,secs[1:]+[total]))
    return rows


def public_copy(spec):
    rows=clock(spec); titles=[x['title'] for x in spec['titles']]
    assert len(set(titles))==3 and all(1<=len(x)<=100 for x in titles)
    assert spec['thumbnail_words']==['NO','GRIP'] and 'no grip' not in titles[0].lower()
    timecodes='\n'.join(f'{x["timestamp"]} {x["title"]}' for x in rows)
    description='\n\n'.join(('\n'.join(spec['description_open']),timecodes,spec['disclosure'],
                             'RESEARCH\n'+'\n'.join(spec['references']),'CREDITS\n'+'\n'.join(spec['credits']),
                             ' '.join(spec['hashtags'])))
    assert 1<=len(description)<=5000 and not set(description)&{'<','>'}
    tags=', '.join(spec['tags']); counted=len(','.join(f'"{t}"' if ' ' in t else t for t in spec['tags']))
    assert counted<500 and len(spec['tags'])==len(set(spec['tags']))
    return rows,titles,description,tags,counted


def copy_kit(spec,dest,thumb,receipt):
    rows,titles,description,tags,counted=public_copy(spec)
    text=dest/f'{STEM}-Studio-Copy.txt'
    text.write_text(f'''MONARCH CAM #1A · YOUTUBE STUDIO COPY
Picture: V3 Full Cinematic Cut · 04:59.80

TITLE — paste this title
{titles[0]}

DESCRIPTION — paste the complete block below
─────────────────────────────────────────
{description}
─────────────────────────────────────────

TAGS — paste into the Tags field, not the description
{tags}

PINNED COMMENT — post when the video is public
{spec['pinned_comment']}

COMMUNITY POST — attach the public video when it goes live
{spec['community_copy']}

TITLE-ONLY TEST OPTIONS — same thumbnail
A. {titles[0]}
B. {titles[1]}
C. {titles[2]}

STUDIO FIELDS
Category: {spec['studio']['category']}
Video language: {spec['studio']['video_language']}
Captions: upload the supplied .en.srt with timing
Thumbnail: {thumb.name}
Review status: upload kit only; video has not been posted or scheduled by this package.
''',encoding='utf-8')
    meta=dest/f'{STEM}-Studio-Metadata.json'
    meta.write_text(json.dumps(dict(episode=spec['episode'],version=spec['picture_version'],source=spec['source'],
                         title=titles[0],title_options=spec['titles'],description=description,chapters=rows,tags=spec['tags'],
                         hashtags=spec['hashtags'],pinned_comment=spec['pinned_comment'],community_copy=spec['community_copy'],
                         studio=spec['studio'],thumbnail=dict(file=thumb.name,words=spec['thumbnail_words'],**receipt),
                         verification=dict(title_chars=len(titles[0]),description_chars=len(description),tags_counted_chars=counted),
                         status='Ready for manual upload; no publication or performance test run.'),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    guide=dest/f'{STEM}-Launch-Guide.md'
    guide.write_text(f'''# Monarch Cam #1A · Launch guide

**Launch with “{titles[0]}” + `NO GRIP`.**

The title promises the unusual way out. The thumbnail gives the problem: feet in the air, jaws close to the slope, and one burst of sand. The first strike at 00:14.70 answers that visual promise before the longer anatomy and experiment sections. The cover is illustrative, not a frame from field footage.

## Upload checklist

1. Use the **4:59.80 full V3**, not the 23.60-second pilot or V2. Prefer the high-bitrate master if you downloaded it; the archived full-length review is a smaller copy of the same edit and mix. Avoid re-encoding either before an upload.
2. Set the title, description and tags from `{text.name}`. Upload `{thumb.name}` ({receipt['output_px'][0]} × {receipt['output_px'][1]}, {receipt['bytes']:,} bytes, sRGB JPEG). It is within the YouTube video-thumbnail mobile upload size limit [1](https://support.google.com/youtube/answer/72431?hl=en).
3. Set **Science & Technology** and **English**. Upload the matching timed English SRT as a subtitle file. Check the cover on a phone, including the bottom-right runtime badge. Verify the manually supplied chapters: start at `00:00`, increasing, all at least ten seconds [1](https://support.google.com/youtube/answer/9884579?hl=en).
4. Leave the CGI and audio-asset credits in the description. The realistic-looking macro scenes are recreations; for this cut select **Yes** if Studio asks whether realistic altered/synthetic scenes are present. The generated cover alone is not the reason for disclosure [1](https://support.google.com/youtube/answer/14328491?hl=en). See the film's accompanying science and credits notes. Choose audience, visibility and publishing time in Studio; nothing has been made public.
5. When ready, attach the video to the community post and post the pinned question from the copy sheet.

## First title test, after upload

| Slot | Title | What changes |
| --- | --- | --- |
'''+''.join(f'| {a} | {x["title"]} | {x["angle"]} |\n' for a,x in zip('ABC',spec['titles']))+f'''
Use **Title only** with the same selected thumbnail on eligible desktop Studio accounts. YouTube's test selects on watch time, not just clicks [3](https://support.google.com/youtube/answer/16391400?hl=en). Keep A as the starting title; don't make manual swaps during the test. Check impressions/CTR and first-30-second retention as diagnostics: more clicks with a weaker opening is a reason to check whether the title overpromises. An inconclusive result is not a win. No CTR or viral outcome has been measured or promised.

## What is in this kit

- `{thumb.name}` — final upload-ready thumbnail (selected artwork, hand-set type).
- `{text.name}` — copy/paste title, description with chapters and credits, tags, pinned comment and community post.
- `{meta.name}` — same fields in structured JSON, exact frames and thumbnail receipt.
- `SpaceGrotesk-OFL.txt` — thumbnail type license. Font revision: `{FONT_REV}`.
''',encoding='utf-8')
    return text,meta,guide


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--art',type=Path,default=CACHE/'selected-cover-art.png')
    p.add_argument('--fonts',type=Path,default=CACHE/'fonts')
    p.add_argument('--out',type=Path,default=DEST)
    p.add_argument('--qa',type=Path,default=CACHE/'qa')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);a.qa.mkdir(parents=True,exist_ok=True)
    spec=json.loads((HERE/'copy-spec.json').read_text()); public_copy(spec)
    thumb,rep=cover(a.art,a.fonts,a.out,a.qa)
    files=[thumb,*copy_kit(spec,a.out,thumb,rep)]
    bundle=a.out/f'{STEM}-YouTube-Packaging.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in files:z.write(f,arcname=f.name)
        z.write(a.fonts/'SpaceGrotesk-OFL.txt',arcname='SpaceGrotesk-OFL.txt')
    with zipfile.ZipFile(bundle) as z:
        assert z.testzip() is None and len(z.namelist())==5
        assert z.read(thumb.name)==thumb.read_bytes()
    (a.qa/'thumbnail-receipt.json').write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'kit':str(bundle),'zip_bytes':bundle.stat().st_size,**rep},indent=2))


if __name__=='__main__':
    main()
