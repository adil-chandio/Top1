#!/usr/bin/env python3
"""Download and verify CC0 / MIT 3D models & PBR textures for EP01 PEHRA.

Sources:
  - Poly Haven (CC0): native Cycles .blend packages and companion texture maps
  - Khronos glTF-Sample-Assets (CC0): GLB binaries
  - mrdoob/three.js (MIT): GLB binaries

The script is deterministic, resumable, and validates byte sizes from the
Poly Haven API so a truncated download never silently reaches Blender.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
UA = "MonarchCinema3D/1.0 (https://github.com/adil-chandio/Top1)"

# Poly Haven CC0 photogrammetry 3D models: (asset_id, preferred_resolution).
# Hero close-up surfaces stay 2k; secondary silhouettes use 1k to keep CI fast.
PH_MODELS = [
    ("sweet_potato", "2k"),
    ("Lantern_01", "2k"),
    ("street_lamp_01", "1k"),
    ("bolt_action_rifle_7_62", "1k"),
    ("chess_set", "1k"),
    ("wooden_candlestick", "1k"),
    ("wicker_basket_01", "1k"),
    ("marble_bust_01", "2k"),
]

# Poly Haven CC0 PBR surface textures: (asset_id, resolution).
PH_TEXTURES = [
    ("dry_mud_field_001", "2k"),
    ("cobblestone_floor_06", "2k"),
]

# Direct CC0 / MIT GLB binaries: local filename -> (url, known byte size).
GLB_ASSETS: dict[str, tuple[str, int]] = {
    "venice_mask.glb": (
        "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/venice_mask.glb",
        4_282_264,
    ),
    "Soldier.glb": (
        "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/Soldier.glb",
        2_160_468,
    ),
    "LeePerrySmith.glb": (
        "https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb",
        404_976,
    ),
    "DiffuseTransmissionPlant.glb": (
        "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/"
        "Models/DiffuseTransmissionPlant/glTF-Binary/DiffuseTransmissionPlant.glb",
        5_759_100,
    ),
    "GlassHurricaneCandleHolder.glb": (
        "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/"
        "Models/GlassHurricaneCandleHolder/glTF-Binary/GlassHurricaneCandleHolder.glb",
        2_705_400,
    ),
    "Lantern.glb": (
        "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/"
        "Models/Lantern/glTF-Binary/Lantern.glb",
        9_564_264,
    ),
}


def http_get_json(url: str) -> dict:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - network retries need broad catch
            last_error = exc
            if attempt < 3:
                print(f"  [retry json {attempt + 1}] {url}: {exc}")
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not fetch JSON {url}: {last_error}")


def download_file(url: str, dest: Path, expected_size: int | None = None) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        if expected_size is None or dest.stat().st_size == expected_size:
            return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    fh.write(chunk)
            if tmp.stat().st_size == 0:
                raise RuntimeError("empty response body")
            if expected_size and tmp.stat().st_size != expected_size:
                raise RuntimeError(f"size mismatch {tmp.stat().st_size} != {expected_size}")
            os.replace(tmp, dest)
            return dest
        except Exception as exc:  # noqa: BLE001 - network retries need broad catch
            last_error = exc
            if tmp.exists():
                tmp.unlink()
            if attempt < 3:
                print(f"  [retry dl {attempt + 1}] {dest.name}: {exc}")
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed downloading {url} -> {dest}: {last_error}")


def collect_ph_model_tasks(asset_id: str, pref_res: str) -> tuple[list[tuple[str, Path, int | None]], dict]:
    data = http_get_json(f"https://api.polyhaven.com/files/{asset_id}")
    blend_section = data.get("blend", {})
    chosen_res = next(
        (r for r in (pref_res, "2k", "1k", "4k") if r in blend_section and "blend" in blend_section[r]),
        None,
    )
    if not chosen_res:
        raise RuntimeError(f"No .blend entry found for Poly Haven model {asset_id}")
    entry = blend_section[chosen_res]["blend"]
    model_dir = ASSETS / "ph_models" / asset_id
    blend_path = model_dir / Path(entry["url"]).name
    tasks: list[tuple[str, Path, int | None]] = [(entry["url"], blend_path, entry.get("size"))]
    for rel_path, meta in entry.get("include", {}).items():
        tasks.append((meta["url"], model_dir / rel_path, meta.get("size")))
    info = {
        "id": asset_id,
        "license": "CC0",
        "source": f"https://polyhaven.com/a/{asset_id}",
        "res": chosen_res,
        "blend": str(blend_path.relative_to(ASSETS)),
        "file_count": len(tasks),
    }
    return tasks, info


def pick_tex_map(data: dict, keys: list[str], res: str, fmts: list[str]) -> tuple[str, int | None, str] | None:
    for key in keys:
        sec = data.get(key)
        if not isinstance(sec, dict):
            continue
        for chosen_res in (res, "2k", "1k"):
            rsec = sec.get(chosen_res)
            if not isinstance(rsec, dict):
                continue
            for fmt in fmts:
                entry = rsec.get(fmt)
                if isinstance(entry, dict) and "url" in entry:
                    return entry["url"], entry.get("size"), fmt
    return None


def collect_ph_texture_tasks(asset_id: str, res: str) -> tuple[list[tuple[str, Path, int | None]], dict]:
    data = http_get_json(f"https://api.polyhaven.com/files/{asset_id}")
    tex_dir = ASSETS / "ph_textures" / asset_id
    tasks: list[tuple[str, Path, int | None]] = []
    maps: dict[str, str] = {}
    spec = {
        "diff": (["Diffuse"], ["jpg", "png"]),
        "nor_gl": (["nor_gl"], ["jpg", "exr", "png"]),
        "rough": (["Rough"], ["jpg", "exr", "png"]),
        "disp": (["Displacement"], ["jpg", "png", "exr"]),
    }
    for slot, (keys, fmts) in spec.items():
        found = pick_tex_map(data, keys, res, fmts)
        if not found:
            print(f"  ! WARNING: {asset_id} has no {slot} map; procedural fallback will be used")
            continue
        url, size, fmt = found
        dest = tex_dir / f"{asset_id}_{slot}.{fmt}"
        tasks.append((url, dest, size))
        maps[slot] = str(dest.relative_to(ASSETS))
    info = {
        "id": asset_id,
        "license": "CC0",
        "source": f"https://polyhaven.com/a/{asset_id}",
        "res": res,
        "maps": maps,
    }
    return tasks, info


def main() -> None:
    t0 = time.time()
    ASSETS.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"models": {}, "textures": {}, "glbs": {}}
    all_tasks: list[tuple[str, Path, int | None]] = []

    print("=== Querying Poly Haven CC0 model manifests ===")
    for aid, res in PH_MODELS:
        tasks, info = collect_ph_model_tasks(aid, res)
        all_tasks.extend(tasks)
        manifest["models"][aid] = info
        print(f"  + model {aid} ({info['res']}): {len(tasks)} files")

    print("=== Querying Poly Haven CC0 PBR texture manifests ===")
    for aid, res in PH_TEXTURES:
        tasks, info = collect_ph_texture_tasks(aid, res)
        all_tasks.extend(tasks)
        manifest["textures"][aid] = info
        print(f"  + texture {aid} ({info['res']}): {', '.join(info['maps'].keys())}")

    print("=== Queueing CC0 / MIT GLB assets ===")
    for fname, (url, size) in GLB_ASSETS.items():
        dest = ASSETS / "glb" / fname
        all_tasks.append((url, dest, size))
        manifest["glbs"][fname] = {
            "path": str(dest.relative_to(ASSETS)),
            "size": size,
            "source": url,
        }

    print(f"=== Downloading {len(all_tasks)} asset files (8 workers) ===")
    total_bytes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_file, url, dest, size): dest for url, dest, size in all_tasks}
        for idx, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            path = fut.result()
            total_bytes += path.stat().st_size
            if idx % 10 == 0 or idx == len(all_tasks):
                print(f"  [{idx}/{len(all_tasks)}] latest={path.name} ({path.stat().st_size / 1048576:.2f} MB)")

    manifest_path = ASSETS / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"=== DONE: {len(all_tasks)} files | {total_bytes / 1048576:.1f} MB "
        f"in {time.time() - t0:.1f}s -> {manifest_path} ==="
    )


if __name__ == "__main__":
    main()
