#!/usr/bin/env python3
"""EP01 PEHRA — full-script shot planner.

Earlier the film was a 15-second excerpt with six shots. This module defines
the full 16-beat storyboard: one scene per beat, timed against the actual
narration, each with its own blocking, practical lights and camera move.

The timeline this emits is the single source of truth for both
``render_scene.py`` (which shot to build) and ``build_audio_full.py`` (where
to place each narration line).

Frame numbers are deliberate: they come from measuring the rendered narration
and adding one second of air per beat, so picture cuts land on the sentence,
not near it.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
FPS = 30


def load_vo_durations(vo_dir: Path) -> dict[str, float]:
    from scipy.io import wavfile

    out = {}
    for p in sorted(vo_dir.glob("b*.wav")):
        sr, data = wavfile.read(str(p))
        out[p.stem] = len(data) / float(sr)
    return out


# Beat sheet: id, slug, narration clip, caption, highlight, palette, camera move.
# Captions are quoted from the narration itself so the lower third always
# matches what the voice is saying at that moment.
BEATS = [
    ("B01_AERIAL_FIELD", "b01", "Khet me aaloo ugaye, bandook wale khade", "bandook", "moon",
     "high drone drift over a guarded field"),
    ("B02_GUARDED_FIELD", "b02", "Chori rokne ke liye nahi", "nahi", "amber",
     "low tracking shot along the guards' boots"),
    ("B03_MASKED_TITLE", "b03", "Log khud aakar chura lein", "chura", "crimson",
     "masked monarch push-in, gate closes behind"),
    ("B04_HUNGRY_PARIS", "b04", "Do sau saal pehle, bhookh", "bhookh", "cold",
     "handheld through a frozen bread queue"),
    ("B05_POTATO_PROMISE", "b05", "Sabse aasaan hal: aaloo", "aaloo", "gold",
     "single potato under a candle, slow orbit"),
    ("B06_POISONED_MIND", "b06", "Janwaron ka khana samajhte the", "janwaron", "cold",
     "potato rolling into a gutter, crowd boots"),
    ("B07_FREE_BASKETS", "b07", "Bazaar me free rakh din", "free", "cold",
     "overturned baskets on wet cobblestones"),
    ("B08_SILENT_PIVOT", "b08", "Samjhana chhoda, game khela", "game", "crimson",
     "mask half-lit, a single clock tick"),
    ("B09_FORTY_ACRES", "b09", "Chaaron taraf shahi fauji", "shahi fauji", "gold",
     "rises over the fenced field at dusk"),
    ("B10_WHISPERS", "b10", "Andar aisa kya ug raha hai?", "kya", "amber",
     "through the fence at a whispering crowd"),
    ("B11_LAST_ORDER", "b11", "Sabse mazedar twist", "twist", "amber",
     "two silhouettes shoulder to shoulder"),
    ("B12_SUNSET_WITHDRAWAL", "b12", "Sooraj doobte hi ghar chale jao", "ghar", "cold",
     "time-lapse sunset to night, guards gone"),
    ("B13_NIGHT_THEFT", "b13", "Deewar kood kar andar ghuse", "deewar", "moon",
     "moonlit wall vault, hands in soil"),
    ("B14_EMPTY_FIELD_DAWN", "b14", "Laakhon logon ki jaan bach gayi", "jaan", "gold",
     "empty field to hundreds of warm windows"),
    ("B15_GRAVE_200_YEARS", "b15", "Phool nahi, aaloo rakh kar", "aaloo", "gold",
     "grave ringed with potato plants, morning mist"),
    ("B16_FINAL_MONARCH", "b16", "Apna pehra lagao", "pehra", "crimson",
     "masked monarch, gate slams shut, silent hold"),
]


def build_timeline(vo_dir: Path, *, lead_s: float = 0.35, tail_s: float = 0.75) -> dict:
    durs = load_vo_durations(vo_dir)
    shots = []
    t = 0.0
    for i, (shot_id, vo, caption, hi, palette, move) in enumerate(BEATS):
        vd = durs.get(vo, 4.0)
        dur = lead_s + vd + tail_s
        # The final beat holds in silence for an extra beat of dead air.
        if shot_id == "B16_FINAL_MONARCH":
            dur += 1.2
        t_start, t_end = t, t + dur
        f_start = int(round(t_start * FPS)) + 1
        f_end = int(round(t_end * FPS))
        shots.append({
            "id": shot_id,
            "vo": vo,
            "vo_start": round(t_start + lead_s, 3),
            "vo_duration": round(vd, 3),
            "caption": caption,
            "highlight": hi,
            "palette": palette,
            "camera": move,
            "t_start": round(t_start, 3),
            "t_end": round(t_end, 3),
            "f_start": f_start,
            "f_end": f_end,
            "lookdev_frame": f_start + max(6, (f_end - f_start) // 2),
        })
        t = t_end

    total = t
    return {
        "tag": "FULL",
        "output_name": "PEHRA_EP01_FULL_1080x1920.mp4",
        "title": "MONARCH · EP01 — PEHRA (full script, dark 3D cinema)",
        "width": 1080,
        "height": 1920,
        "fps": FPS,
        "duration_sec": round(total, 3),
        "total_frames": int(round(total * FPS)),
        "shots": shots,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--vo-dir", default=str(BASE / "vo_full"))
    ap.add_argument("--out", default=str(BASE / "build" / "timeline_full.json"))
    args = ap.parse_args()

    timeline = build_timeline(Path(args.vo_dir))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    print(f"=== {len(timeline['shots'])} beats · {timeline['duration_sec']}s · "
          f"{timeline['total_frames']} frames -> {out} ===")
    for s in timeline["shots"]:
        print(f"  {s['f_start']:4d}-{s['f_end']:4d}  {s['id']:24s} "
              f"{s['t_start']:6.2f}-{s['t_end']:6.2f}s  {s['caption']}")


if __name__ == "__main__":
    main()
