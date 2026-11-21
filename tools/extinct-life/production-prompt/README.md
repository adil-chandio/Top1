# 3D Video Production Master Prompt

`master-prompt.md` is the single source. `build_pdf.py` produces a selectable A4 PDF and a UTF-8 copy/paste companion with the same instructions. The output goes under `deliverables/3d-video-production/` by default, separate from the film archive. Nothing in this build renders video or requires production media.

## Rebuild the document

Run from the repository root with Python 3.11+. The PDF builder needs ReportLab 4.4.6 and FontTools 4.60.1. Place the four pinned font files in `.cache/production-prompt/fonts/` or pass `--fonts <directory>`:

- `Fraunces.ttf`, `PlexSans.ttf`, `PlexMono.ttf`: source paths, revisions, SHA-256 and license paths are in `../step-4/asset-lock.json`.
- `SpaceGrotesk.ttf`: `google/fonts`, `ofl/spacegrotesk/SpaceGrotesk[wght].ttf` at `5bd87dfc525c8a0d1d8529d3684716e00c3fc59a`, also pinned in `../short/reedit/prepare_reedit.py`. Retain the source OFL notices when caching the font files.

```sh
python3 -m pip install --target .cache/production-prompt/python 'reportlab==4.4.6' 'fonttools==4.60.1'
PYTHONPATH="$PWD/.cache/production-prompt/python" python3 tools/extinct-life/production-prompt/build_pdf.py
```

`--out` overrides the delivery directory. The builder checks font hashes and fails on page overflow. The PDF's contents links, folios and schematic figures are layout aids; the TXT contains the complete prompt. After changing copy or layout, inspect rendered pages and check PDF text extraction against the source, especially type sizes, tables, glyphs, and the beginning and end of the prompt.
