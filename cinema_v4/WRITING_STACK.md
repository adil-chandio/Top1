# MONARCH WRITING STACK — best repos, verified
## Viral script writing ke liye jo repos actually kaam ke hain
**Date:** 15 Nov 2026 · 14 query families · ~70 repos screened · 6 files pulled offline

---

# 0. Inclusion rule (guess nahi)

Repo list me tab hi aaya jab: **(a)** license clear tha (MIT/CC0/Apache), **(b)** star count + recent push, **(c)** maine uske **asli files khol kar** dekha ke andar usable material hai. Sirf description par bharosa nahi kiya.

---

# 1. THE STACK — 6 tiers

## Tier 1 · ANTI-SLOP (sab se important)
| Repo | Stars | License | Kya hai (verified) |
|---|---|---|---|
**`blader/humanizer`** | **★69.3k** | MIT | `SKILL.md` me **26 numbered AI tells** — §1 "Not X but Y", §2 one-line closers, §6 forced triads, §8 dashes, §12 stock words, §13 inflated significance, §19 bold as decoration. Har tell ke saath *watch for / problem / before / after* |
**`Nanako0129/sepia`** | ★3.8k | MIT | De-AI writing skill, plugin system |
**`howshannon/slop-cop`** | ★11 | MIT | Slop ko **grade** karta hai (audit + rewrite) |
**`Jakeschincariol/…-agent-skill` → `ig-human`** | ★6.5k | MIT | `slop.json`: 154 stock words + 16 structural tells + 18 invisible chars |

> **Yehi wajah hai ke aapne "AI slop" pakda.** Maine apne script isi lexicon par chalaye — 3 tells nikle.

## Tier 2 · HOOK (pehla 1.5 second)
| Repo | Stars | License | Kya hai (verified) |
|---|---|---|---|
**`vyralcontent/content-skills`** | ★229 | MIT | **Three-layer hook** (visual + verbal + text + audio), `hook-archetypes.md` me **Kane Kallaway ke 6 archetypes** (Fortuneteller / Experimenter / Teacher / Magician / Investigator / Contrarian) + MrBeast ka "title-thumbnail contract" |
**`rediumvex/viral-hooks-skill`** | ★131 | MIT | **100 hook formulas**, 10 psychology triggers me organized (curiosity gap, contrarian, loss aversion…) |
**`Jakeschincariol/instagram-agent-skill`** | ★6.5k | MIT | **26 scored hook formulas** + `hookscore.py` (hook ko 0–100 score) + `beats.py` (timed beat sheet) |

## Tier 3 · NARRATIVE / FILM LEVEL
| Repo | Stars | License | Kya hai (verified) |
|---|---|---|---|
**`jtydhr88/screenwriting-skills`** | ★2.1k | MIT | Chekhov dramaturgy (10 structural + 10 character patterns), Ozu style, Succession writers'-room. Isme: **S4 "open and close in the same place"** (loop), **S5 "the right answer is said in act one and rejected"**, **S8 "three-layer ending: hopeful line + nihilist's line + mundane action"**, **C4 "one object + one catchphrase per character"** |
**`5263jh/POV-AI-Storytelling`** | ★178 | NOASSERTION | First-person visual story framework |
**`bkingfilm/lapian-notes`** | ★794 | MIT | Film breakdown: **emotion curve + structure tree** extraction |

## Tier 4 · PERSUASION
| Repo | Stars | License | Kya hai |
|---|---|---|---|
**`MADEVAL/MindFluence`** | ★85 | MIT | **20 cognitive biases → copy** playbooks |
**`WynterJones/CoppieGPT`** | ★166 | none | 232 copywriting frameworks |
**`avectats7/copy-that-sells`** | ★25 | MIT | Print/OOH/headline craft |

## Tier 5 · PLATFORM PACKAGING
`sergebulaev/instagram-skills` ★841 MIT · `kostja94/marketing-skills` ★1106 MIT (160+ skills) · `AgriciDaniel/claude-youtube` ★776 MIT (retention scripts) · `blacktwist/social-media-skills` ★656 MIT

## Tier 6 · RESEARCH (evidence, guess nahi)
`fendouai/ViralForge` ★189 Apache-2.0 (viral video **deconstruct** karta hai: hook + script breakdown) · `sharon-laicc/viral-video-decomposer` ★13 MIT (shot-level breakdown) · `instagram-agent-skill/ig-viral` (**outlier multiple** method)

### Rejected (aur kyun)
| Repo | Kyun nahi |
|---|---|
`remotion-dev/remotion` ★73k | License: 4+ logon ki org ke liye paid — MIT alternative (`motion-canvas`) maujood |
`jamriska/ebsynth` ★1.7k | Painterly look = "cheap AI" feel, raw-content rule ke khilaf |
`zenstory-ai/drama-skills` ★4.3k | Chinese short-drama pipeline — hamare vertical ke liye overkill |
Generic "prompt packs" | Koi scoring, koi gate nahi — bas text dher |

---

# 2. Jo maine offline le aaya — `cinema_v4/refs/`

| File | Source | Size |
|---|---|---|
`humanizer_26_tells.md` | blader/humanizer | 32 KB |
`slop_lexicon.json` | instagram-agent-skill | 22 KB |
`three_layer_hook.md` | vyralcontent | 5.2 KB |
`hook_archetypes.md` | vyralcontent | 7.9 KB |
`100_hook_formulas.md` | rediumvex | 15 KB |
`chekhov_dramaturgy.md` | screenwriting-skills | 34 KB |

Sab MIT — repo me rakh sakte hain, build me use kar sakte hain.

---

# 3. Ab ye theory nahi — gate hai

`cinema_v4/tools/script_qc.py` — script ko scan karta hai, **score deta hai, fail par exit 1**.

```
python3 cinema_v4/tools/script_qc.py script.txt --duration 45 --register film
```

Checks: hook ≤6 words · forced triads (anaphora allowed) · fragment closers · banned clichés · CTA bait · disfluency (voice-note register) · concrete numbers · sentence-length variance · abstract-noun density · pace · word count.

**Proof ke ye kaam karta hai:** mere hi do scripts par chalaya —
- `film_v6.txt` → **64/100 FAIL** (triad, fragment closer, 0 numbers)
- `kal_v1.txt` → **80/100 PASS** (1 triad baaki = fix karna hai)

Yani ab main apne aap ko pass nahi kar sakta. Tool karayega.

---

# 4. MONARCH WRITING PIPELINE — 7 stages

| Stage | Kaam | Repo/tool | Gate |
|---|---|---|---|
**1 EVIDENCE** | niche ke 3x outliers nikaalo (views ÷ account median) | `ig-viral` method, `ViralForge` | 10 outliers, na milen to mat likho |
**2 IDEA** | topic par 4 tests: retell · image · reframe · accusation | apna (`IDEA_SLATE.md`) | chaaron pass |
**3 HOOK** | 3 layers: visual + verbal + text (+ audio) | `three_layer_hook.md`, 26+100 formulas | `hookscore` ≥ 70 |
**4 STORY** | lie → want → need → wound → volta → ending | `chekhov_dramaturgy.md` (S4/S5/S8/C4) | volta maujood, need kabhi nahi boli |
**5 VOICE** | insaan ki zubaan, register ke hisaab se | `humanizer_26_tells.md`, `slop.json` | **0 tells** §1/§2/§6 |
**6 GATE** | number se score | `script_qc.py` | **≥ 80** |
**7 SHOOT** | shots/sound timing | `beats.py` rhythm + apna SFX bank | har cue ±1 frame |

---

# 5. Chekhov se 3 cheezein jo `KAL` me direct lagengi

| Pattern | Kya | Hamare script me |
|---|---|---|
**S4** "open and close in the same place" | shuruaat aur aakhir **ek hi jagah** | khaali kursi → wohi kursi, ab bhare hue |
**S5** "right answer act one me bola jaata hai aur reject hota hai" | sach pehle, inkaar baad me | *"kal koi din nahi hai"* — woh sunta hai, maanta nahi |
**S8** "three-layer ending: hope + nihilist + mundane action" | teen layer ka close | *"main abhi bhi apni taraf hoon"* (hope) + **[POP]** (nihilist) + **pen uthana** (mundane) |

**Aur C4:** ek character = **ek object + ek catchphrase**. Hamare paas: **kursi** + **"kal se."**

---

# 6. Agla step

1. Aap **woh asli object** batao (kursi ki jagah) — asli detail ke bagair script sach nahi hogi
2. Main `KAL` ko is pipeline se **dobara** likhunga (stage 3→6) aur QC score dikhaunga
3. Score ≥80 → aapki awaaz → SFX bank + pop → 6 look-dev stills
