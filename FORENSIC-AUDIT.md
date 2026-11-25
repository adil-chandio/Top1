# Top1 Repository — Deep Forensic Audit

**Date:** 2026-11-25 · **Branch:** `arena/96d9eaf9-top1` · **Base:** `f51c0c6` · **Mode:** read-only analysis (no production code changed)

---

## 0. Executive summary (Bhai, seedha khatka)

Ye repo do alag cheezon ka mixed bag hai:

1. **Aik clean, production-ish static storefront + screening site** — 4 public pages, 5 MP4 films, local prompt builder, no backend, no checkout. Ye hissa genuinely healthy hai: `npm ci`, `npm test` (101/101), `npm run build` sab pass, 188 local HTML references me se **0 broken**, syntax/JSON errors **0**, `npm audit` **0 vulnerabilities**.
2. **Aik bahut bada experimental "AI cinema lab"** — ~66,000 lines of Python/JS/C++, nine parallel video pipelines, 21 JSON schemas, dozens of manifests/receipts, V6 "IMAX" SDK. Ye hissa rich hai lekin governance, portability aur verification discipline kamzor hai.

**Sabse bade 5 issues (priority order):**

| # | Issue | Severity |
|---|---|---|
| 1 | `AGENTS.md`/`CLAUDE.md` deprecated folders ko ban karte hain, lekin `README.md`, `package.json` aur 4 test files unhi folders par chalte hain — agent ke liye contradictory constitution | **High** |
| 2 | Current branch par **zero CI**: 3 workflow sirf purane branch `arena/6e66724e-top1` par trigger hote hain; koi build/test gate nahi | **High** |
| 3 | `long_v6` ke 3 Python tests fresh checkout me **fail** hote hain (hardcoded `/home/user/Top1`, `/tmp/...`, missing gitignored exports, aur `captions` vs `total_caption_cues` key mismatch) | **High** |
| 4 | `qa-skeleton.js` jab real probe overrides diye jate hain to bhi `honestyNote` me jhooth bolta hai "no probe has run"; aur override sirf `{status:'ok'}` se poora QA pass ban jata hai | **Medium-High** |
| 5 | `claims-rights.js` me `id`-less rights entry ko `ok: true` bol ke `entries` se drop kar diya jata hai — schema usi entry ko reject karta hai | **Medium** |

**Verdict:** Storefront ko ship kiya ja sakta hai (preview ke taur par, checkout band ke saath). Cinema-lab ko "production pipeline" bolna abhi premature hai — usko portabilize + CI me lana zaroori hai.

---

## 1. Exact inventory (kya-kya hai isme)

| Category | Count | Details |
|---|---:|---|
| Tracked files | **561** | ~66.5 MB tracked; `.git` ~59 MB; full workspace after install ~240 MB |
| Top-level tools | **17 entries** | 12 folders + 5 root `.mjs` scripts |
| Python files | **133** | 7 `test_*.py`, 3rd-party heavy scripts |
| JS files | **98** | + 33 `.mjs` |
| JSON files | **95** | 21 JSON schemas, 13 `*-receipt*.json` manifests |
| Markdown docs | **62** | README, AGENTS, CLAUDE, production bibles, research notes |
| HTML pages | **15** | 4 public + 11 internal render/preview pages |
| MP4 assets | **5** | `public/demos/` — reflector alone 19.5 MB |
| GLB assets | **9** | huayuan (6), cockroach v4 humans (3) |
| Shell scripts | **8** | mostly old native render/encode scripts |
| Shell CSS | **4** | `src/styles.css`, `src/demos.css`, studio CSS ×2 |
| JS unit tests | **17 files / 101 tests** | `test/*.test.js`, all green |
| Python test files | **7** | research-system, rig, V6 SDK, V4/V5/V6 gates |

### 1.1 Public app (4 routes)

| Route | Entry | Kya karta hai |
|---|---|---|
| `/` | `index.html` + `src/main.js` | Hero, 4 Cinema Cuts, kit cards, prompt builder, free sample, custom brief dialog, FAQ, film player dialog |
| `/kit.html` | `kit.html` | Starter Kit preview — 6-step outline, sample download (same `main.js`, defensive bail-outs) |
| `/monarch-studio/` | `monarch-studio/index.html` + `studio.js` | Project 001 *Who Crushed the Can?*, 11 chapter cues, PRODUCTION.md download |
| `/monarch-studio/reflector/` | `.../index.html` + `project.js` | Project 002 *The Light With No Battery*, 18 chapter cues, research audit |

Shared small modules: `src/prompts.js` (3 languages×formats×durations template engine), `src/demos.js` + `src/air-crush.js` + `src/reflector.js` (film metadata/cues), `src/demo-player.js` + `monarch-studio/screening.js` (players), `vite.config.js` (MPA + directory redirects).

### 1.2 Tools (11 logical groups)

1. **`monarch-v6-imax-sdk/`** — "mandatory" engine: PBR/shadow, post-FX (ACES, Vogel bokeh, anamorphic bloom), physics/VFX, parametric sculpt + IK, WOFF2 HUD, WebSocket raw-RGBA renderer, audio DSP, forensic MP4 validator.
2. **`monarch-cockroach/`** — gold-standard references: `short_v6` (1,050 frames @30 = 35 s loop), `long_v6` (9,008 frames @30 ≈ 300.27 s, 35 cuts + f0, 7 chapters), plus old v3/v4/v5/feature.
3. **`extinct-studio/`** — zero-dependency governance substrate: 14 schemas, subset validator, 15-state forward-only machine, 100-point scorecard, 8-category claims classifier, rights manifest rules, honest QA skeleton.
4. **`monarch-studio-os/`** — parallel older governance: 7 schemas, Python validators (claim linter, state machine, full-decode media QA), SQLite research warehouse.
5. **`extinct-life/`** — 128 files: 9-step documentary pipeline, research desk/probe, report bridge, Python/C++ renderers, receipt JSONs.
6. **`extinct-channel/`** — huayuan project: `.glb` creatures/rocks, lookdev, film page, critique notes.
7. **`monarchs-edit/`** — Desi 3D explainer P1/E1/long + research CSVs, illustrative (not measured) disclaimers.
8. **`gecko/`** — creature rig/natural edit/premiere — legacy but still unit-tested.
9. **`monarch-ant/`, `-v2/`, `-v3/`** — pre-V6 ant prototypes.
10. **`demo-render/` + root scripts** — the actual source of the 5 shipped films: Three.js compositor, motion models, soundtrack/VO mixing, verify tools.
11. **`docs/`** — V6 production bible and case study; `public/samples/` — editable worked examples and 1,200-frame reflector audit CSV.

### 1.3 Data/contracts

* `src/*.js` film descriptors are the runtime source of truth for shots/captions/presets; `index.html` duplicates the card markup and MP4 hrefs manually.
* 21 JSON schemas + 13 receipts encode provenance/hashes/locks; 14 of them (extinct-studio) are checked by `test/extinct-studio-schemas.test.js`.
* CI: 3 workflows (research desk, connectivity probe, encrypted report bridge) — all branch-pinned to a **different** branch than this one.

---

## 2. Verification log (maine khud chalaya)

| Check | Command | Result |
|---|---|---|
| Dependency install | `npm ci` | ✅ 18 packages, 0 vulnerabilities |
| JS tests | `npm test` | ✅ **101/101**, 0 fail/skip, 3.13 s |
| Production build | `npm run build` | ✅ 19 modules, 4 entries, 490 ms |
| Broken local refs | custom scan of 188 `src`/`href` in 15 HTML files | ✅ 0 broken |
| JSON parse | all tracked `.json` | ✅ 0 invalid |
| JS syntax | `node --check` on all `.js`/`.mjs` | ✅ 0 failures |
| Python syntax | `python3 -m compileall` | ✅ 0 failures |
| Shell syntax | `bash -n` on 8 `.sh` | ✅ 0 failures |
| Python stdlib tests | `unittest` research-system + `test_rig` | ✅ 12 + 10 = **22 pass** |
| Python pytest subset | 5 V6/OS files, `-k 'not end_to_end'`, deps in `/tmp/pydeps` | ⚠️ **17 pass, 7 skip, 3 FAIL** (all `long_v6`) |
| UI smoke (jsdom) | `?demo=air-crush`, chips, submit, brief dialog | ✅ preset load, validation gating, disabled-copy logic, brief generation all behaved as designed |
| Secret scan | env names/token patterns/private key files | ✅ no literal API keys/private keys committed |

**Note:** browser E2E with real Chromium was not run — no Chromium binary in the sandbox. jsdom stubs `showModal`/`scrollIntoView`; results above describe pure DOM logic only.

---

## 3. Forensic findings (severity ordered)

### F1 — Documentation constitution contradicts the runnable repo — **High**

* `AGENTS.md:7-15` and `CLAUDE.md:5`: `tools/demo-render/`, `tools/gecko/`, `tools/monarchs-edit/`, `tools/extinct-life/`, `tools/monarch-ant*` are **deprecated — "NEVER copy or run"**.
* But `README.md:77-84` tells you to rebuild shipped films from `tools/demo-render/` via `npm run render:demos`.
* `package.json:11` defines `render:demos` → `tools/render-demos.mjs`, which imports `demo-render` modules.
* `test/air-crush.test.js`, `test/film-motion.test.js`, `test/reflector.test.js` import `tools/demo-render/*`; `test/gecko*.test.js`, `test/desi-3d-*.test.js` import `tools/gecko/*` and `tools/monarchs-edit/*`.
* So an agent obeying AGENTS.md literally will refuse to run the exact code the repo's own tests and README require.

**Fix:** split the constitution into "active runtime (storefront + shipped film sources)" vs "historical reference only"; whitelist the tested modules explicitly instead of a blanket ban.

### F2 — No CI on this branch; no build/test gate — **High**

All 3 workflows trigger only on `arena/6e66724e-top1`:
* `.github/workflows/extinct-life-research-system.yml:4-9`
* `...research-probe.yml:4-8`
* `...report-bridge.yml:2-5`

Nothing runs `npm ci && npm test && npm run build` on `main` or on `arena/96d9eaf9-top1`. A broken build or failing JS test could land silently. The pinned action SHAs and least-privilege `permissions` are good, but are attached to the wrong branch.

### F3 — `long_v6` Python gates fail in a fresh checkout — **High**

Exact failure from the audit run:

```
FAILED long_v6/test_long_v6.py::test_voice_lock_and_captions_integrity   FileNotFoundError: .../exports/...Captions-V6-IMAX.srt
FAILED long_v6/test_long_v6.py::test_protected_climax_windows_zero_overlays   FileNotFoundError: /tmp/v6_long/build/overlays/...
FAILED long_v6/test_long_v6.py::test_master_mp4_forensic_imax_gate   AssertionError: Missing Master MP4: /tmp/v6_long/...
3 failed, 17 passed, 7 skipped, 1 deselected
```

Root causes:
* `test_long_v6.py:19-28` hardcodes `/home/user/Top1` and `/tmp/v6_long/...` instead of `Path(__file__).resolve()`.
* Gitignored `exports/` and `/tmp` artifacts are required; unlike `short_v6`/`v4` gates there is **no `pytest.skip`** when they are absent.
* `test_long_v6.py:54` checks `lock.get("captions", [])`, but the lock file actually stores **`total_caption_cues: 81`** and no `captions` array. The `or open(SRT_PATH)` fallback then throws before it can help.
* Same non-portability pattern appears in `render_short_v6.mjs:13-29`, `render_imax_ws.mjs:25-46`, `build_audio_v4.py:17-19`, etc. Count: **126 absolute-path references across 30 tracked files**.
* Bonus gap: `media_qa.py` imports `av` and `pyloudnorm`, neither installed by `bootstrap_v6_runtime.sh:132-134`.

**Fix:** derive `ROOT` from `__file__`, skip when optional artifacts are absent, read the correct key, add `av`/`pyloudnorm` to documented requirements.

### F4 — QA skeleton can lie while still looking honest — **Medium-High**

`tools/extinct-studio/qa-skeleton.js:83-92` always returns:

> "No render, media decode or audio probe has run. Every check is reported as unavailable ... This skeleton is not a QA pass."

I injected real-looking `{status:'ok'}` overrides for all 20 checks; result: `overall.ok = 20`, `qaPasses = true`, `toGateReceipt → {videoOk:true, audioOk:true, unchecked:[]}` — but `honestyNote` still said no probe ran. Also `runSkeleton` accepts overrides with `observed: null`, so the `qa-passed` gate (`state-machine.js:...qaReports`) can be flipped without any measurement.

**Fix:** make `honestyNote` conditional on actual tally; require non-null `observed` evidence (or an explicit `evidenceId`) before accepting an `ok` override.

### F5 — Rights validator drops id-less entries — **Medium**

`tools/extinct-studio/claims-rights.js:148-155`: an entry passes `validateRightsEntry`, but is only pushed to `entries` when `entry.id != null`. Verified:

```js
validateRights({entries:[{sourceType:'font',url:'https://example.org',license:'MIT',commercialAllowed:true,accessDate:'2026-11-21'}]})
// → { ok: true, errors: [], entries: [] }
```

Yet `schemas/rights.json.schema.json:25-31` marks `id` as **required**. Two validators disagree; a malformed manifest can be called valid and silently vanish from the returned register. `validateClaims` similarly does not check duplicate claim IDs or that `evidenceIds` exist in a sources register (that check only exists in the parallel Python linter).

### F6 — Subset validator has three latent holes — **Low/Medium**

`tools/extinct-studio/validate.js`:
* `anyOf` (lines 72-80) returns early, so sibling `type`/`enum`/`pattern` on the same node are ignored. Current 14 schemas don't combine them, so no live failure — but adding one would silently weaken validation.
* Invalid regex in `pattern` is swallowed by an empty `catch` (line ~84) despite the comment promising an error.
* `$ref`/`definitions` are listed as known keys but not implemented. Current schemas avoid `$ref`, so again latent only.

### F7 — Two parallel governance stacks — **Medium**

`extinct-studio/state-machine.js` (JS, 15 states, gates, never sets `published` from tools) and `monarch-studio-os/validators/state_machine.py` (Python, same 15 states, `HUMAN_ONLY_STATES`) encode overlapping but different rules. `extinct-studio/validate.js` is a hand-rolled subset validator while `test_studio_os.py` uses full `jsonschema`. Nothing reconciles them; a project can satisfy one and contradict the other. Same theme: `qa-skeleton.js` vs `media_qa.py`, `claims-rights.js` vs Python `claim_linter`.

### F8 — Dead weight / duplication — **Low/Medium**

* `public/art/hero.jpg` (91 KB) is not referenced by any source file yet is copied into `dist/`.
* `posterAt`, `color`, `tag`, `lines`, `caption` in film descriptors are mostly render-time metadata; the web player uses only `id`, `title`, `asset`, `duration`, `width`, `shots[].jumpTo/shotNote`, `preset`.
* Card markup in `index.html` duplicates `src/demos.js` data; adding a film means editing both.
* 5 MP4s + 9 GLBs + 6 source-era pipelines live in Git (~40 MB in `public/`, ~11 MB in `extinct-channel/`), even though AGENTS.md:67-68 says heavy masters should stay out of Git.
* Font license files exist in `public/licenses/` and ship in `dist/`, but no page links to them.

### F9 — Performance / UX details — **Low**

* Good: video `preload="none"`, posters only, JS bundle ~8 kB + 12.4 kB shared, fonts/art local, 44 px+ touch targets, skip links, `:focus-visible`, mobile-first grids.
* Gaps: hero/gallery posters are single fixed-size images (no `srcset`); `prefers-reduced-motion` is handled only in `monarch-studio/studio.css:169`, not in `src/styles.css`/`src/demos.css`; the film dialog closes only via its × button / Escape — no backdrop-click handler in `src/demo-player.js`.

### F10 — Security & privacy posture — **Mostly good, 3 caveats**

Good: no literal API keys or private keys tracked; all 5 YouTube key aliases are passed via `secrets.*` env vars; `research.py` uses `NoRedirect`, size caps (3 MB) and strips error bodies; `probe.py` deliberately avoids printing key names/URLs; `npm audit` clean; app inserts user text via `.value`/`textContent` only (no `innerHTML`, no `eval`, no network calls in the storefront).

Caveats:
1. `extinct-life-report-bridge.yml:14-19` pins a hard-coded `run-id: 44991315768` and emits base64 CMS chunks as **public** `::notice` annotations. The X.509 certificate is embedded in the public workflow; only the private key (generated in `.cache`, 2-day lifetime) protects the payload. No plaintext/key is committed — but this is an unusual public-log transport and should be treated as time-limited, not as secure storage.
2. `tools/extinct-channel/projects/huayuan/PROJECT-STATUS.md:7-14` embeds four Google Drive document/video IDs. The privacy linter `claim_linter.py:22-26` would flag such IDs, but its test only scans `monarch-studio-os/` and `monarch-cockroach/` (`test_studio_os.py:139`), so this file is outside the check. If "no Drive IDs in Git" is the policy, these need review; if they are intentional public review links, document the exception.
3. `bootstrap_v6_runtime.sh` installs unpinned npm/pip versions into `/tmp` (`package.json` written with `^` ranges, pip without constraints) — reproducibility/supply-chain risk, not a live exploit.

### F11 — Correctness details in the V6 hard rules — **Informational**

Claims checked out where they can be checked statically: `short_v6` = 1,050 frames @30 fps; `long_v6` = 9,008 frames, 36 cut indices (f0 + 35 cuts); `verify_imax_mp4` streams O(1) frames and checks black frames, A-B-A flicker, loop MAE, LUFS and peak. But two inconsistencies: AGENTS.md:63 requires `-14.2 LUFS` / `-1.0 dBFS`, while `forensic_qa_sdk.py:24,113-115` accepts `-15.4..-13.2 LUFS` / `<= -0.9 dBFS`; the doc also demands `alimiter=limit=0.708` on AAC, while the shipped `render-demos.mjs:36` uses `limit=0.89` for narrated films. Different product lines, but the "non-negotiable" wording is not literally universal.

---

## 4. What is genuinely well done (credit where due)

* **Clean separation:** static MPA storefront has no server, no keys, no DB; dialogs degrade to plain MP4 links without JS; custom brief explicitly says "nothing sent".
* **Honest framing everywhere:** prompts say "return a plan, not a rendered video"; films labelled visualization/fictional; P1/E1 labelled illustrative, not test results; research reports label missing sources instead of fabricating winners; QA skeleton defaults to `unavailable`.
* **Receipt culture:** hashes, voice locks, frame counts, shot-cut sets and provenance JSONs make claims auditable rather than vibes-based.
* **Testing depth:** 101 JS tests cover shot timing, optics math, physics invariants, schema/fixture consistency, studio cross-links; 22 stdlib Python tests cover rig invariants and research honesty.
* **Accessibility basics:** skip links, focus rings, 44 px targets, `aria-live`/`role=status`, `aria-pressed` toggles, reduced-motion in studio, no broken local refs.
* **No secrets in Git**, pinned GitHub Actions SHAs, least-privilege workflow permissions.
* **Strong refactor discipline:** V6 SDK genuinely centralizes shaders/post-FX/renderer; gold-standard short/long references exist with concrete frame numbers.

---

## 5. Recommended action order (agar fix karna ho)

**P0 (this week)**
1. Rewrite `AGENTS.md`/`CLAUDE.md` deprecation list to whitelist the modules `npm test`/`render:demos` actually use.
2. Add a CI workflow on `main` + all `arena/**` branches: `npm ci && npm test && npm run build`.
3. Fix `test_long_v6.py` (relative ROOT, correct `total_caption_cues` key, `pytest.skip` when artifacts absent).

**P1**
4. Make `qa-skeleton` honesty note dynamic; require evidence for `ok` overrides.
5. Require `id` in `validateRights` and check duplicate IDs + evidence references.
6. Decide one canonical governance stack (prefer `extinct-studio` JS + `jsonschema`-compatible validator) and adapt the other as a thin adapter.

**P2**
7. Replace 126 hardcoded paths with env vars/`Path(__file__)`; pin bootstrap versions; declare `av`/`pyloudnorm`.
8. Generate demo cards from `DEMOS` data instead of duplicated HTML; remove unused `hero.jpg`; move master media out of Git if the <128 MiB rule matters.
9. Add reduced-motion rules and backdrop-click close to the storefront; consider `srcset` for posters; link font licenses in the footer.
10. Review the Drive IDs and the public-log report bridge against an explicit written privacy policy.

---

## 6. Audit limits (imandari se)

* No 3D frame was rendered and no MP4 was decoded during this audit (no Chromium/FFmpeg binary available here), so visual quality, audio loudness and decoded-frame claims are **not independently verified** — only their source code and test contracts were inspected.
* External research claims (papers, YouTube metadata, "viral" evidence) were not re-fetched; they are recorded in the repo as manifests/receipts.
* The V6 end-to-end pytest (which bootstraps a large `/tmp` runtime and renders) was deliberately not executed in full.
* This is a read-only audit: only `FORENSIC-AUDIT.md` was added; no application or tool code was modified.
