#!/usr/bin/env python3
"""Render the Atlantic Tracks opening comparison from pinned map data.

Requires Python 3.11+, Pillow 11.3 and pyshp 2.3.1. No fossil images are included.
125 Ma is an example reconstruction, not a measured age or a migration route.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import shapefile
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

REPO = Path(__file__).resolve().parents[3]
MAIN = Path(__file__).resolve().parent
CACHE = REPO / ".cache/monarch-extinct/atlantic-tracks/sources"
EXPORT = REPO / "deliverables/extinct-life-step-2"
FONTS = Path("/usr/share/fonts/truetype/dejavu")
NAME = "Extinct-Life-Atlantic-Tracks-Opening-Board.png"
SCALE = 2
SIZE = (1920, 1080)
AGE = 125.0
# Passagem das Pedras geosite and centre of the published Koum Basin bounds.
# These markers represent regions, not the position of any pictured print.
SITES = ((-6.734270096, -38.262065887), (8.291666666666666, 14.516666666666667))
PLATES = (201, 701)
EXTENT = (-85.0, -38.0, 41.0, 30.0)  # west/south/east/north, same scale for both panels
GOLD = "#f6c580"
JADE = "#97e3d0"
INK = "#f4f4ea"
MUTED = "#a9bbb8"
PAPER = "#0c1519"
OCEAN = "#132c36"
PANEL = "#101f23"
LINE = "#30454b"


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def unit(lat, lon):
    lat, lon = map(math.radians, (lat, lon))
    return math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def quaternion(lat, lon, angle):
    half = math.radians(angle) / 2
    return math.cos(half), *(math.sin(half) * x for x in unit(lat, lon))


def product(a, b):
    w, x, y, z = a
    t, i, j, k = b
    return (
        w * t - x * i - y * j - z * k,
        w * i + x * t + y * k - z * j,
        w * j - x * k + y * t + z * i,
        w * k + x * j - y * i + z * t,
    )


def interpolate(a, b, t):
    """Shortest-arc interpolation of finite rotation quaternions."""
    cosine = dot(a, b)
    if cosine < 0:
        cosine = -cosine
        b = tuple(-x for x in b)
    if cosine > 0.9995:
        result = tuple((1 - t) * x + t * y for x, y in zip(a, b, strict=True))
        return tuple(x / math.sqrt(dot(result, result)) for x in result)
    theta = math.acos(cosine)
    return tuple(
        (math.sin((1 - t) * theta) * x + math.sin(t * theta) * y) / math.sin(theta)
        for x, y in zip(a, b, strict=True)
    )


def get_rotations(path):
    rotations = {201: [], 701: []}
    for line in path.read_text().splitlines():
        fields = line.split("!", 1)[0].split()
        if len(fields) == 6 and fields[0] in ("201", "701"):
            plate, time, lat, lon, angle, parent = fields
            rotations[int(plate)].append((float(time), int(parent), quaternion(*map(float, (lat, lon, angle)))))
    return rotations


def reconstruction(plate, age, rotations):
    """Only the South America -> Africa -> absolute anchor chain is needed."""
    if plate == 0:
        return (1, 0, 0, 0)
    rows = rotations[plate]
    before = max((r for r in rows if r[0] <= age), key=lambda r: r[0])
    after = min((r for r in rows if r[0] >= age), key=lambda r: r[0])
    assert before[1] == after[1] == {201: 701, 701: 0}[plate]
    local = before[2] if before[0] == after[0] else interpolate(before[2], after[2], (age - before[0]) / (after[0] - before[0]))
    return product(reconstruction(before[1], age, rotations), local)


def rotated(lat_lon, q):
    inverse = q[0], *(-x for x in q[1:])
    _, x, y, z = product(product(q, (0, *unit(*lat_lon))), inverse)
    return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))


def separation(sites):
    cosine = dot(*(unit(*site) for site in sites))
    return 6371.0088 * math.acos(max(-1, min(1, cosine)))


def polygons(geometry):
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    raise ValueError(f"Unsupported land geometry: {geometry['type']}")


def contains(point, ring):
    lat, lon = point
    inside = False
    start = ring[-1]
    for end in ring:
        a, b = start
        x, y = end
        if (b > lat) != (y > lat) and lon < a + (lat - b) * (x - a) / (y - b):
            inside = not inside
        start = end
    return inside


def land_ids(point, all_land):
    return {idx for idx, (outer, *holes) in enumerate(all_land) if contains(point, outer) and not any(contains(point, hole) for hole in holes)}


def sbox(values):
    return tuple(round(x * SCALE) for x in values)


def position(site, width, height):
    lat, lon = site
    w, s, e, n = EXTENT
    return (lon - w) / (e - w) * width, (n - lat) / (n - s) * height


def draw_map(land, width, height, early):
    out = Image.new("RGB", sbox((width, height)), OCEAN)
    d = ImageDraw.Draw(out)
    fill = "#456759" if early else "#3b6765"
    coast = "#719577" if early else "#608c83"
    w, s, e, n = EXTENT
    # The chart omits the poles and doesn't cross the antimeridian. Pillow
    # clips the layer to its own bounds, so no shape can leak into the cards.
    for outer, *holes in land:
        if max(p[0] for p in outer) < w or min(p[0] for p in outer) > e or max(p[1] for p in outer) < s or min(p[1] for p in outer) > n:
            continue
        d.polygon([sbox(position((y, x), width, height)) for x, y in outer], fill=fill, outline=coast, width=SCALE)
        for ring in holes:
            d.polygon([sbox(position((y, x), width, height)) for x, y in ring], fill=OCEAN, outline=coast, width=SCALE)
    grid = Image.new("RGBA", out.size)
    dg = ImageDraw.Draw(grid)
    for lon in range(-80, 41, 20):
        x, _ = position((0, lon), width, height)
        dg.line(sbox((x, 0, x, height)), fill=(178, 200, 201, 37), width=SCALE)
    for lat in range(-20, 21, 20):
        _, y = position((lat, 0), width, height)
        dg.line(sbox((0, y, width, y)), fill=(178, 200, 201, 37), width=SCALE)
    return Image.alpha_composite(out.convert("RGBA"), grid).convert("RGB")


def render(current, early, paleo, output, font_dir):
    im = Image.new("RGB", sbox(SIZE), PAPER)
    d = ImageDraw.Draw(im)
    regular = font_dir / "DejaVuSans.ttf"
    bold = font_dir / "DejaVuSans-Bold.ttf"
    mono = font_dir / "DejaVuSansMono-Bold.ttf"

    def text(x, y, value, size, color=INK, face=regular, anchor="lt"):
        d.text(sbox((x, y)), value, fill=color, font=ImageFont.truetype(str(face), size * SCALE), anchor=anchor)

    def leader(a, b, tone):
        d.line(sbox((*a, *b)), fill=tone, width=SCALE * 2)

    def marker(x, y, tone):
        r = 10
        d.ellipse(sbox((x - r - 3, y - r - 3, x + r + 3, y + r + 3)), fill=PAPER)
        d.ellipse(sbox((x - r, y - r, x + r, y + r)), fill=tone, outline=INK, width=SCALE)

    def label(x, y, title, subtitle, tone, anchor="lt"):
        text(x, y, title, 27, tone, bold, anchor)
        text(x, y + 35, subtitle, 21, INK, regular, anchor)

    d.rectangle(sbox((72, 57, 107, 64)), fill=GOLD)
    text(126, 49, "EXTINCT LIFE   /   OPENING STUDY", 22, GOLD, mono)
    text(1848, 51, "01  /  ATLANTIC TRACKS", 20, MUTED, mono, "rt")
    text(72, 99, "The ocean between the tracks", 64, INK, bold)
    text(75, 184, "Two dinosaur track regions, seen on a modern map and in an Early Cretaceous reconstruction.", 26, MUTED)

    # Original generalized three-toed outline. It is not traced from either
    # site and does not encode specimen measurements or a stride direction.
    d.rounded_rectangle(sbox((1512, 102, 1848, 216)), radius=12 * SCALE, fill=PANEL, outline=LINE, width=SCALE)
    outline = (
        (46, 90), (38, 87), (32, 80), (30, 68), (23, 60), (14, 54),
        (7, 46), (2, 35), (3, 29), (8, 26), (15, 29), (24, 37),
        (34, 46), (36, 43), (35, 29), (37, 14), (42, 4), (46, 1),
        (50, 5), (53, 16), (54, 29), (53, 43), (56, 46), (65, 37),
        (76, 29), (85, 25), (90, 27), (91, 33), (86, 42), (77, 50),
        (65, 58), (60, 67), (60, 77), (56, 85), (51, 89),
    )
    d.polygon([sbox((1538 + x * .94, 116 + y * .94)) for x, y in outline], fill="#263c3b", outline="#a9bdb7", width=2 * SCALE)
    text(1642, 135, "THREE-TOED TRACK", 19, INK, mono)
    text(1642, 164, "Schematic only", 19, MUTED)

    for x, dataset, sites, k, headline, sub, take in (
        (72, current, SITES, "01   /   PRESENT DAY", "≈6,000 km apart", "Approximate distance today", "An ocean separates the track regions."),
        (978, early, paleo, "02   /   EARLY CRETACEOUS", "≈1,000 km apart", "Study estimate • 125 Ma model view", "The regions were on one connected landmass."),
    ):
        ancient = x > 72
        d.rounded_rectangle(sbox((x, 243, x + 870, 934)), radius=15 * SCALE, fill=PANEL, outline=LINE, width=SCALE)
        text(x + 24, 267, k, 20, GOLD if not ancient else JADE, mono)
        text(x + 24, 308, headline, 48, INK, bold)
        text(x + 26, 372, sub, 23, MUTED)
        m_x, m_y, width, height = x + 22, 413, 826, 446
        im.paste(draw_map(dataset, width, height, ancient), sbox((m_x, m_y)))
        d.rectangle(sbox((m_x, m_y, m_x + width, m_y + height)), outline=LINE, width=SCALE)
        markers = [tuple(offset + px for offset, px in zip((m_x, m_y), position(site, width, height), strict=True)) for site in sites]
        if not ancient:
            text(x + 354, 708, "ATLANTIC", 20, "#b1c8cc", mono)
            a, b = markers
            leader(a, (a[0] - 48, a[1] + 45), GOLD)
            label(x + 120, a[1] + 55, "Sousa Basin", "Brazil", GOLD)
            leader(b, (b[0] + 20, b[1] - 53), JADE)
            label(x + 790, b[1] - 116, "Koum Basin", "Cameroon", JADE, "rt")
        else:
            text(x + 354, 773, "WESTERN GONDWANA", 21, "#d8e3d5", mono)
            a, b = markers
            leader(a, (a[0] - 42, a[1] - 61), GOLD)
            label(x + 440, a[1] - 123, "Sousa region", "Future Brazil", GOLD, "rt")
            leader(b, (b[0] + 36, b[1] + 46), JADE)
            label(x + 801, b[1] + 55, "Koum region", "Future Cameroon", JADE, "rt")
        for site, color in zip(markers, (GOLD, JADE), strict=True):
            marker(*site, color)
        text(x + 24, 887, take, 25, INK, bold)

    d.line(sbox((72, 967, 1848, 967)), fill=LINE, width=SCALE)
    text(73, 985, "Distances: Jacobs et al. (2024). Dots mark approximate regions, not a trackway. 125 Ma is a model snapshot, not a track date.", 19, MUTED)
    text(73, 1017, "Maps: Natural Earth (public domain); Kocsis & Scotese PaleoCoastlines v7.1 (CC BY 4.0; cropped, recolored and annotated).", 18, MUTED)

    png = im.resize(SIZE, Image.Resampling.LANCZOS)
    notes = PngInfo()
    notes.add_text("Title", "Extinct Life: The ocean between the tracks — opening study")
    notes.add_text("Sources", "Natural Earth v5.1.2; Kocsis and Scotese 2021 (doi:10.1016/j.earscirev.2020.103463) v7.1 CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); distances: Jacobs et al. 2024")
    png.save(output, pnginfo=notes, optimize=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", type=Path, default=CACHE)
    p.add_argument("--out", type=Path, default=EXPORT)
    p.add_argument("--fonts", type=Path, default=FONTS)
    args = p.parse_args()
    provenance = json.loads((MAIN / "map-sources.json").read_text())
    for entry in provenance["inputs"]:
        candidate = args.sources / entry["name"]
        if not candidate.is_file() or digest(candidate) != entry["sha256"]:
            raise SystemExit(f"Missing or changed source: {candidate}. See map-sources.json for pinned inputs.")

    natural = json.loads((args.sources / "ne_110m_land.geojson").read_text())
    current = [g for f in natural["features"] for g in polygons(f["geometry"])]
    with (args.sources / "125Ma_CS_v7.shp").open("rb") as f:
        early = [g for shape in shapefile.Reader(shp=f).iterShapes() for g in polygons(shape.__geo_interface__)]
    rotations = get_rotations(args.sources / "m06c9h_3id_forPgeog_19o_r1c.rot")
    for point, plate in zip(SITES, PLATES, strict=True):
        recovered = rotated(point, reconstruction(plate, 0, rotations))
        assert all(abs(a - b) < 1e-9 for a, b in zip(point, recovered, strict=True))
    paleo = tuple(rotated(x, reconstruction(i, AGE, rotations)) for x, i in zip(SITES, PLATES, strict=True))
    today_a, today_b = [land_ids(point, current) for point in SITES]
    then_a, then_b = [land_ids(point, early) for point in paleo]
    assert today_a and today_b and today_a.isdisjoint(today_b), (today_a, today_b)
    assert then_a & then_b, (then_a, then_b)
    assert 5900 < separation(SITES) < 6200 and 950 < separation(paleo) < 1300
    assert all(EXTENT[0] < x < EXTENT[2] and EXTENT[1] < y < EXTENT[3] for y, x in (*SITES, *paleo))
    args.out.mkdir(parents=True, exist_ok=True)
    proof = args.out / NAME
    render(current, early, paleo, proof, args.fonts)
    print(json.dumps({
        "output": str(proof),
        "sha256": digest(proof),
        "dimensions": list(SIZE),
        "model_age_ma": AGE,
        "present_region_points_lat_lon": SITES,
        "paleo_region_points_lat_lon": paleo,
        "present_model_separation_km": round(separation(SITES), 1),
        "paleo_model_separation_km": round(separation(paleo), 1),
        "different_modern_land_polygons": True,
        "same_early_model_land_polygon": True,
        "distances_on_board_are_study_summaries_not_model_measurements": True,
    }, indent=2))


if __name__ == "__main__":
    main()
