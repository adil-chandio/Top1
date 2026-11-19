# Google Drive — Setup aur Structure

## Sabse pehle: 2 traps

### ❌ Trap 1 — Service account + My Drive = kaam nahi karega
Service accounts ka **apna storage quota nahi hota**. Personal Gmail ke My Drive mein upload karne ki koshish par quota error aata hai.

### ❌ Trap 2 — "shared with me" folder mein upload
Service account ko folder share karo to wo upload nahi kar sakta properly (ownership issues).

---

## Do sahi raste

### A. Workspace + Shared Drive (recommended)

```
1. Buyer ka Google Workspace account (paid, ~$6/user/mo)
2. Shared Drive banao: "Channel-Renders"
3. Service account banao (Google Cloud Console)
4. Shared Drive ke member banao as Content Manager
5. Service account ko Drive API enable
6. JSON key server par rakho (repo mein NAHI)
```

✅ No consent screen, no token expiry, permanent.
⚠️ Workspace chahiye — free Gmail se nahi hoga.

### B. OAuth as user (normal Gmail ke liye)

```
1. Google Cloud project + OAuth consent screen
2. Scope: https://www.googleapis.com/auth/drive.file  (sabse kam permission)
3. Buyer ek baar consent deta hai
4. Refresh token save karo (encrypted)
5. Upload on behalf of user
```

✅ Free Gmail bhi chalega.
⚠️ Token revoke ho sakta hai → error handling + re-auth flow chahiye.
⚠️ `drive.file` scope mein sirf woh files dikhengi jo app ne banayi — ye aapke liye kaafi hai.

**Recommendation:** Pilot buyer ke saath **A** try karo. Nahi chala to **B**.

---

## Folder structure (from day 1 — badalna mushkil hoga)

```
Channel-Renders/                      ← Shared Drive
├── _system/
│   ├── config.json                   niche, language, models
│   ├── episodes.json                 master list
│   └── status.csv                    log, human readable
│
├── 2026-11-19_pressure-cooker/       ← ek episode = ek folder
│   ├── final.mp4                     1080×1920 H.264 faststart
│   ├── poster.webp
│   ├── captions.srt
│   ├── script.md
│   ├── shot-plan.json
│   └── qa-report.json               duration, loudness, decode, hash
│
├── 2026-11-22_bicycle-reflector/
│   └── ...
│
└── _archive/
```

**Rules:**
1. Folder name: `YYYY-MM-DD_slug` — sorting free milta hai
2. `final.mp4` ka naam har jagah same — automation aasan
3. Kuch bhi delete nahi — `_archive/` mein move karo
4. `status.csv` mein har episode ka row

---

## status.csv format

```csv
episode,title,status,created,renderMinutes,cost_usd,driveLink,qaPass
2026-11-19_pressure-cooker,How a Pressure Cooker Works,delivered,2026-11-19,52,0.31,https://...,true
2026-11-22_bicycle-reflector,Why Reflectors Glow,rendered,2026-11-22,88,0.44,https://...,true
```

Status values: `idea` → `scripted` → `planned` → `rendered` → `qa_passed` → `delivered`

Buyer ko yahi file sabse zyada pasand aati hai — ek nazar mein poora channel dikh jata hai.

---

## manifest.json (per episode)

```json
{
  "episode": "2026-11-19_pressure-cooker",
  "generated": "2026-11-19T14:02:00Z",
  "pipeline": { "version": "0.1.0", "models": ["cooker"], "moves": ["reveal","cutaway","mechanism","quantity","compare","payoff"] },
  "files": {
    "final.mp4": { "bytes": 15234000, "sha256": "..." },
    "poster.webp": { "bytes": 84200, "sha256": "..." },
    "captions.srt": { "bytes": 3120, "sha256": "..." }
  },
  "tech": { "width": 1080, "height": 1920, "fps": 24, "durationSec": 29.0, "videoCodec": "h264", "audioCodec": "aac", "loudnessLufs": -14.5 },
  "qa": { "decodePass": true, "faststart": true, "captionBounds": true, "claimsUnsure": 0 }
}
```

**Ye file aapka proof hai.** Client ke saath dispute ho to yahi dikhana hai.

---

## Security

- Service account JSON key **kabhi repo mein nahi** (`.env` already ignored)
- Buyer ki OAuth token **encrypted** rakho (Supabase vault ya local encrypted file)
- `drive.file` scope use karo — full `drive` scope mat maango, buyer darr jayega
- Har upload ke baad `status.csv` update, warna log kho jayega

---

## Test karna (pehle din)

```sh
# Ye script aapke credentials se ek test folder bana kar upload karti hai
node services/tools/drive-check.mjs
```

Ye script credentials **mange gi nahi** — sirf batayegi ke `.env` mein kya chahiye aur kya missing hai. Asli upload aap khud verify karo.

**Pehla test:** ek 1 KB text file upload karo apne test folder mein, delete karo. Agar yahi fail ho to pipeline kabhi nahi chalega.
