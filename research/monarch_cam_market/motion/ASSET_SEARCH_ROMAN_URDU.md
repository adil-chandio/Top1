# Asset search aur actual import receipt

## Nayi progress

Pichhla procedural model reuse nahi kiya. GitHub repository/code searches aur source files read karke naya candidate download/import/render kiya:

- Repository: https://github.com/dgreenheck/tidewater
- Inspected HEAD: `4811ba48d795197de5621985f404e765c0b7c0ef` (source downloads used contents API HEAD, not pinned retrieval; hashes below audit actual bytes).
- Root `LICENSE`: MIT, Copyright 2026 DRG Software Solutions LLC.
- `CREDITS.md`: humpback ko original procedural model kehta hai; NOAA public-domain illustration se side-profile tracing described. Root notice retained alongside downloaded files. Yeh source ka provenance statement hai, independent legal certification nahi.
- Files: `public/models/whale/humpback.bin`, `.json`, `_albedo.png`, `_height.png`.
- Geometry actually imported: 40,212 vertices, 79,870 triangles, original UV and texture maps. Geometry ka procedural origin khud quality guarantee nahi.
- Native shader-rig weights available in binary; conventional skeleton/Blender rig abhi nahi bana. Porting and deformation validation pending.

## Test result

`inspect_tidewater.py` ne Blender Cycles mein isolated whale render ki. Pehle image par top-side white patch dikha; upstream data-texture loading inspect karke UV V-axis convention correct ki. Second render visually inspected: white ventral pigmentation ab underside par hai; long pectorals, defined jaw, dorsal/tail contour pichhle rejected proxy se zyada readable. Lighting abhi flat; texture grooves repeated/striped; eye/rostrum detail and exact anatomy approval pending. Selected AI concept ki fidelity abhi matched nahi.

No image delivered as a substitute for requested video. `out/tidewater_inspection.png` internal inspection only. No motion tested, no 20-second MP4 made. No render process left running.

## Other bounded candidates

- `sciom/whales_3d_supplementary/GEOMETRY_LICENCES.md`: humpback CC BY-NC-SA; monetized-film route ke liye accept nahi kiya. Different whale species ko humpback substitute nahi kiya.
- `hafewa/UnityFishAnimation`: whale FBX + textures listed; README source is Unity Asset Store humpback-whale-3547. Root licence null; copied repository ko independent reuse licence nahi maana. Assets not downloaded.
- `Edu-Art-3D/Eduart-whale-3D`: root licence null; reuse held.
- `Trudes808/Whale-Image-Data-Factory/THIRD_PARTY.md`: K9239 High-Poly Humbpack Whale Sketchfab asset reportedly CC BY 4.0; static/no skeleton; files not included. Original provider not verified/downloaded in this environment. Not claimed rights-cleared.

## Next engineering work

Port native deformation weights/pectoral bases into Blender, test multiple swimming poses and look for mesh collapse or attachments sliding. Orca asset/rig still unresolved. Only after those checks should 480-frame/24fps motion proof render start. Existing requested 20-second target unchanged; full-film approval not implied.
