#!/usr/bin/env python3
"""Lay out the same master prompt as a selectable PDF and UTF-8 text."""
from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import math
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from fontTools.ttLib import TTFont as VariableFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = '3D-Video-Production-Master-Prompt'
W, H = A4
LEFT = 49
RIGHT = W - LEFT
WIDTH = RIGHT - LEFT
PAPER = '#FCFAF4'
INK = '#1D302F'
DARK = '#112C2B'
FOREST = '#245A51'
MOSS = '#4D675F'
PALE = '#E9F0E9'
CREAM = '#F4EFE2'
LINE = '#CDD4C9'
COPPER = '#A85B35'
MINT = '#B4CEBE'
LIGHT = '#F7F4E8'
FONT_PINS = {
    'Fraunces.ttf': '177ff6c0f14e5550a3c624247cd1189611d4eb65d000b14944c63d967958abbb',
    'PlexSans.ttf': '3b031aa4216174205bd8471f88a49b91f093169e9e87bd5262242bc5967fe2e3',
    'PlexMono.ttf': 'a9b4c49bb299e05b5f6c481e7fb5e78943d2793249a0c8874ab574a2d1ea6755',
    'SpaceGrotesk.ttf': 'acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72',
}
NAV = (
    'Production brief', 'Actual tools', 'Evidence & animatic', 'Voice & timing',
    'Geometry, contact & light', 'Maps & kinetic type', 'Camera & edit', 'Foley & mix',
    'Proof & render', 'Conform & QC', 'Measured benchmarks', 'Tested upgrades',
    'Review & handoff',
)


def register_fonts(folder: Path):
    for name, pin in FONT_PINS.items():
        p = folder / name
        if not p.is_file() or sha256(p.read_bytes()).hexdigest() != pin:
            raise ValueError(f'Missing or mismatched pinned font: {p}')
    pdfmetrics.registerFont(TTFont('Mono', str(folder / 'PlexMono.ttf')))
    with TemporaryDirectory() as tmp:
        variants = (
            ('Display', 'Fraunces.ttf', {'opsz': 39, 'wght': 560, 'SOFT': 12, 'WONK': 1}),
            ('Body', 'PlexSans.ttf', {'wght': 400, 'wdth': 100}),
            ('Strong', 'PlexSans.ttf', {'wght': 650, 'wdth': 100}),
            ('Tech', 'SpaceGrotesk.ttf', {'wght': 650}),
        )
        for alias, src, axes in variants:
            with VariableFont(folder / src) as variable:
                frozen = instantiateVariableFont(variable, axes, inplace=False)
                # Distinct PostScript names keep the two Plex instances from
                # being merged into a single PDF subset by the compositor.
                frozen['name'].setName(f'ProductionPrompt-{alias}', 6, 3, 1, 1033)
                frozen['name'].setName(f'ProductionPrompt-{alias}', 6, 1, 0, 0)
                dest = Path(tmp) / f'{alias}.ttf'
                frozen.save(dest)
            pdfmetrics.registerFont(TTFont(alias, str(dest)))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='Strong', italic='Body', boldItalic='Strong')


def read_prompt(source: Path):
    pages = []
    for page in re.split(r'^%% ', source.read_text(encoding='utf-8'), flags=re.M)[1:]:
        label, title, *lines = page.strip().splitlines()
        if not title.startswith('# '):
            raise ValueError(f'No heading in {label}')
        blocks = []
        for line in lines:
            if not line:
                continue
            if line.startswith('| '):
                row = tuple(s.strip() for s in line.strip('|').split('|'))
                if blocks and blocks[-1][0] == 'table':
                    blocks[-1][1].append(row)
                else:
                    blocks.append(('table', [row]))
                continue
            for kind, pattern in [('sub', r'### (.+)'), ('list', r'((?:- |\d+\. ).+)'), ('note', r'> (.+)')]:
                if match := re.fullmatch(pattern, line):
                    blocks.append((kind, match[1]))
                    break
            else:
                blocks.append(('body', line))
        pages.append((label, title[2:], blocks))
    if len(pages) != len(NAV):
        raise ValueError(f'Navigation expects {len(NAV)} sections, got {len(pages)}')
    return pages


INLINE = re.compile(r'`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*')


def inline(s, markup=False):
    if not markup:
        return INLINE.sub(lambda m: next(x for x in m.groups() if x is not None), s)
    pos, parts = 0, []
    for m in INLINE.finditer(s):
        parts.append(escape(s[pos:m.start()]))
        if m[1] is not None:
            parts.append(f'<font name="Mono" color="{FOREST}" size="9.4">{escape(m[1])}</font>')
        elif m[2] is not None:
            parts.append(f'<font name="Strong">{escape(m[2])}</font>')
        else:
            parts.append(f'<font name="Strong" color="{FOREST}">{escape(m[3])}</font>')
        pos = m.end()
    return ''.join(parts) + escape(s[pos:])


def text_prompt(pages):
    lines = []
    for _, title, blocks in pages:
        lines.extend([title, ''])
        for kind, s in blocks:
            if kind == 'table':
                lines.extend(' | '.join(map(inline, row)) for row in s)
            else:
                lines.append(inline(s))
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def rule(c, x1, x2, y, color=LINE, size=.55):
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(size)
    c.line(x1, y, x2, y)


def text(c, x, y, s, font='Body', size=11.25, color=INK, tracking=0):
    c.saveState()
    t = c.beginText(x, y)
    t.setFont(font, size)
    t.setFillColor(HexColor(color))
    t.setCharSpace(tracking)
    t.textLine(s)
    c.drawText(t)
    c.restoreState()


def render_relief(c):
    """Decorative wireframe heightfield, not footage or a measured specimen."""
    c.saveState()
    clip = c.beginPath()
    clip.rect(357, H-208, W-357, 192)
    c.clipPath(clip, stroke=0)

    def project(u, v):
        eroded = -.25 * math.exp(-((u-.04)/.30)**2-((v+.12)/.38)**2)
        ridge = .083 * math.cos(4*u-1.5*v) + .065*math.sin(5*v+2*u)
        return 504 + 99*u + 49*v, H-111 + 49*v - 27*u + 120*(eroded+ridge)

    for along in (True, False):
        for i in range(17):
            k = -1 + 2*i/16
            c.setLineWidth(.56 if i % 4 == 0 else .28)
            c.setStrokeColor(HexColor('#719887' if i % 4 == 0 else '#3D635A'))
            p = c.beginPath()
            for j in range(61):
                q = -1 + 2*j/60
                x, y = project(q, k) if along else project(k, q)
                (p.moveTo if not j else p.lineTo)(x, y)
            c.drawPath(p)
    x, y = project(.18, .35)
    c.setStrokeColor(HexColor('#E6AA78'))
    c.setFillColor(HexColor('#E6AA78'))
    c.setLineWidth(.65)
    c.circle(x, y, 2.4, fill=1, stroke=0)
    c.circle(x, y, 7, fill=0, stroke=1)
    c.line(x, y+7, x, y+25)
    c.line(x, y+25, x+24, y+25)
    c.restoreState()


def header(c, i, label, title):
    c.setFillColor(HexColor(PAPER))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.bookmarkPage(f'section-{i}')
    c.addOutlineEntry(f'{i:02d}  {title}', f'section-{i}', level=0)
    if i == 1:
        c.setFillColor(HexColor(DARK))
        c.rect(0, H-202, W, 202, stroke=0, fill=1)
        render_relief(c)
        text(c, LEFT, H-39, 'PRODUCTION WORKFLOW  /  ORIGINAL CGI', 'Mono', 8.6, MINT, .95)
        text(c, LEFT-1, H-92, '3D Video Production', 'Display', 36, LIGHT)
        text(c, LEFT-1, H-136, 'Master Prompt', 'Display', 42, LIGHT)
        text(c, LEFT, H-170, 'Atlantic Tracks: Cinema Edition + Short 01 V2', 'Tech', 11, MINT)
        rule(c, LEFT, LEFT+88, H-201.5, '#DBA773', 1.6)
        return H-225
    text(c, LEFT, H-30, '3D VIDEO PRODUCTION   /   MASTER PROMPT', 'Mono', 8, MOSS, .7)
    text(c, RIGHT-62, H-30, 'CONTENTS', 'Mono', 8, FOREST, .6)
    c.linkRect('', 'section-1', (RIGHT-66, H-35, RIGHT, H-20), relative=0, thickness=0)
    rule(c, LEFT, RIGHT, H-44)
    group, detail = label.split(' / ', 1)
    num = f'{i:02d}'
    c.setFillColor(HexColor(FOREST))
    c.roundRect(LEFT, H-80, 25, 19, 3.5, fill=1, stroke=0)
    text(c, LEFT+6.7, H-74, num, 'Mono', 9.5, LIGHT)
    text(c, LEFT+36, H-74, f'{group}  /  {detail}', 'Mono', 8.2, MOSS, .6)
    title_size = min(29.5, 29.5 * WIDTH / pdfmetrics.stringWidth(title, 'Display', 29.5))
    text(c, LEFT-1, H-116, title, 'Display', title_size)
    return H-137


def footer(c, i, total):
    rule(c, LEFT, RIGHT, 47)
    text(c, LEFT, 29, 'VIDEO PRODUCTION ONLY', 'Mono', 7.7, MOSS, .8)
    for j in range(total):
        x = W / 2 - (total-1)*4 + j*8
        rule(c, x-2.1, x+2.1, 32, COPPER if j+1 == i else LINE, 1.9)
    c.setFont('Mono', 8.5)
    c.setFillColor(HexColor(MOSS))
    c.drawRightString(RIGHT, 29, f'{i:02d} / {total:02d}')


def style(font='Body', size=11.5, leading=15, color=INK):
    return ParagraphStyle('p', fontName=font, fontSize=size, leading=leading,
                          textColor=HexColor(color), splitLongWords=True, allowWidows=0, allowOrphans=0)


def add_block(c, kind, s, y):
    if kind == 'table':
        cols = len(s[0])
        widths = [123, WIDTH-123] if cols == 2 else [90, (WIDTH-90)/2, (WIDTH-90)/2]
        if any(len(row) != len(widths) for row in s):
            raise ValueError(f'Malformed {cols}-column table')
        items = [[Paragraph(inline(cell, True), style(
            'Tech' if r == 0 else 'Strong' if j == 0 else 'Body',
            10.55, 13.55, LIGHT if r == 0 else INK)) for j, cell in enumerate(row)]
            for r, row in enumerate(s)]
        obj = Table(items, colWidths=widths, style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(FOREST)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor(PALE), HexColor('#F4F5ED')]),
            ('LINEBELOW', (0, 1), (-1, -1), .45, HexColor(LINE)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 11),
            ('RIGHTPADDING', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 7.6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7.6),
        ]))
        _, h = obj.wrap(WIDTH, H)
        obj.drawOn(c, LEFT, y-h)
        return y-h-14
    if kind == 'note' and s in ('BEGIN PROMPT', 'END OF PROMPT'):
        if s == 'END OF PROMPT':
            rule(c, LEFT, RIGHT, y-3)
            y -= 12
        text(c, LEFT, y-10, s, 'Mono', 9.2, COPPER, 1)
        return y-22
    if kind == 'sub':
        y -= 2
        obj = Paragraph(inline(s, True), style('Tech', 13.4, 17.4, FOREST))
        _, h = obj.wrap(WIDTH, H)
        obj.drawOn(c, LEFT, y-h)
        return y-h-5.5
    if kind == 'note':
        obj = Paragraph(inline(s, True), style('Body', 11.25, 14.8))
        _, h = obj.wrap(WIDTH-31, H)
        box = h+21
        c.setFillColor(HexColor(PALE))
        c.roundRect(LEFT, y-box, WIDTH, box, 4, fill=1, stroke=0)
        c.setFillColor(HexColor(COPPER))
        c.rect(LEFT, y-box+6, 2, box-12, fill=1, stroke=0)
        obj.drawOn(c, LEFT+15, y-h-10.5)
        return y-box-10
    if kind == 'list':
        bullet, s = s.split(' ', 1)
        c.setFillColor(HexColor(COPPER))
        if bullet == '-':
            c.circle(LEFT+4, y-7, 1.7, fill=1, stroke=0)
        else:
            text(c, LEFT, y-10.8, bullet, 'Mono', 9.4, COPPER)
        x = LEFT+17
    else:
        x = LEFT
    obj = Paragraph(inline(s, True), style())
    _, h = obj.wrap(RIGHT-x, H)
    obj.drawOn(c, x, y-h)
    return y-h-(8 if kind == 'list' else 10)


def contact_figure(c, y):
    y -= 7
    rule(c, LEFT, RIGHT, y)
    text(c, LEFT, y-16, 'CONTACT STATES', 'Tech', 10.6, FOREST)
    text(c, RIGHT-150, y-16, 'SCHEMATIC / NOT TEST DATA', 'Mono', 8.4, MOSS, .23)
    card_w = (WIDTH-28)/5
    for i, (label, lift, bend) in enumerate(zip(
        ('APPROACH', 'CONTACT', 'LOAD', 'RELEASE', 'AFTERMATH'),
        (11, 0, -6, 11, None), (0, 1.5, 8, 9, 11), strict=True,
    )):
        x, ground = LEFT+i*(card_w+7), y-72
        c.setFillColor(HexColor(PALE))
        c.roundRect(x, y-90, card_w, 64, 4, fill=1, stroke=0)
        center = x+card_w*.50
        p = c.beginPath()
        p.moveTo(x+7, ground)
        p.lineTo(center-27, ground)
        p.curveTo(center-14, ground+bend*.22, center-17, ground-bend, center, ground-bend)
        p.curveTo(center+16, ground-bend, center+14, ground+bend*.36, center+27, ground)
        p.lineTo(x+card_w-7, ground)
        c.setStrokeColor(HexColor(FOREST))
        c.setLineWidth(.95)
        c.drawPath(p)
        rule(c, x+7, x+card_w-7, ground-13, LINE, .45)
        if lift is not None:
            base = ground+lift
            p = c.beginPath()
            p.moveTo(center-12, base+18)
            p.lineTo(center-4, base+18)
            p.curveTo(center-3, base+13, center-7, base+8, center+1, base+6)
            p.curveTo(center+12, base+6, center+17, base+5, center+18, base+2)
            p.curveTo(center+17, base, center+9, base, center-7, base)
            p.curveTo(center-15, base+.6, center-16, base+5, center-13, base+10)
            p.close()
            c.setFillColor(HexColor('#76A394' if i != 2 else '#A85B35'))
            c.drawPath(p, fill=1, stroke=0)
        if i in (1, 2):
            c.setFillColor(HexColor('#C58354'))
            c.circle(center+11, ground+lift-1, 2, fill=1, stroke=0)
        text(c, x+6, y-105, f'{i+1:02d}  {label}', 'Mono', 8.3, MOSS, .12)
    return y-109


def safe_figure(c, y):
    y -= 8
    box_h = 105
    c.setFillColor(HexColor(PALE))
    c.roundRect(LEFT, y-box_h, WIDTH, box_h, 4, fill=1, stroke=0)
    x, yy, w = LEFT+20, y-95, 48
    h = w * 16/9
    c.setFillColor(HexColor(DARK))
    c.roundRect(x, yy, w, h, 3, fill=1, stroke=0)
    # Project the actual reference bounds, with top-left origin in video.
    sx, sy = x+68*w/1080, yy+h-1538*h/1920
    sw, sh = (932-68)*w/1080, (1538-214)*h/1920
    c.setStrokeColor(HexColor(MINT))
    c.setLineWidth(.6)
    c.rect(sx, sy, sw, sh, stroke=1, fill=0)
    c.setStrokeColor(HexColor('#D6A375'))
    c.setDash(2, 1.4)
    c.line(sx+4, sy+sh*.23, sx+sw-4, sy+sh*.23)
    c.setDash()
    c.circle(sx+sw*.54, sy+sh*.6, 3, fill=0, stroke=1)
    tx = LEFT+89
    text(c, tx, y-24, 'V2 PORTRAIT SAFE AREA', 'Tech', 11.2, FOREST)
    text(c, tx, y-46, '(68, 214)–(932, 1538) on a 1080 × 1920 frame', 'Mono', 9.2)
    text(c, tx, y-66, 'Keep kinetic type in the legible lane and clear of the action.', 'Body', 11.25)
    text(c, tx, y-84, 'REFERENCE ONLY  /  CHECK THE INTENDED INTERFACE', 'Mono', 8.15, MOSS, .32)
    return y-box_h


def contents(c, y):
    y -= 5
    rule(c, LEFT, RIGHT, y)
    text(c, LEFT, y-19, 'CONTENTS', 'Tech', 11.4, FOREST)
    text(c, LEFT+85, y-19, 'One prompt. Fill the brief and use all sections.', 'Body', 10.55, MOSS)
    y -= 37
    for j, label in enumerate(NAV[1:], 2):
        row, col = divmod(j-2, 3)
        x = LEFT + col * (WIDTH/3)
        baseline = y - row*18.5
        text(c, x, baseline, f'{j:02d}', 'Mono', 8.4, COPPER)
        text(c, x+19, baseline, label, 'Body', 10.6, INK)
        c.linkRect('', f'section-{j}', (x-1, baseline-5, x+WIDTH/3-6, baseline+11), relative=0, thickness=0)
    return y-70


def build(source, fonts, out):
    pages = read_prompt(source)
    register_fonts(fonts)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / f'{NAME}.pending.pdf'
    c = Canvas(str(tmp), pagesize=A4, invariant=1, pageCompression=1, lang='en')
    c.setTitle('3D Video Production Master Prompt')
    c.setSubject('An original CGI production workflow grounded in Atlantic Tracks')
    c.showOutline()
    for i, (label, title, blocks) in enumerate(pages, 1):
        y = header(c, i, label, title)
        for kind, s in blocks:
            y = add_block(c, kind, s, y)
        if i == 1:
            y = contents(c, y)
        elif label.startswith('SCENE /'):
            y = contact_figure(c, y)
        elif label.startswith('PICTURE /'):
            y = safe_figure(c, y)
        if y < 61:
            raise ValueError(f'Text overflows page {i} ({label}): lower bound {y:.1f}')
        footer(c, i, len(pages))
        c.showPage()
        print(f'{i:02d} {y:6.1f} pt  {title}')
    c.save()
    tmp.replace(out / f'{NAME}.pdf')
    (out / f'{NAME}.txt').write_text(text_prompt(pages), encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=HERE / 'master-prompt.md')
    p.add_argument('--fonts', type=Path, default=ROOT / '.cache/production-prompt/fonts')
    p.add_argument('--out', type=Path, default=ROOT / 'deliverables/3d-video-production')
    args = p.parse_args()
    build(args.source, args.fonts, args.out)
