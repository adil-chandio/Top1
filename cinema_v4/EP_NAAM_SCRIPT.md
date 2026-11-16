# "NAAM LO" · EP script · **55 s** · 195 words

**v6 — chhota, tez, aur gehra.** (v5 tha 62 s / 222 words.)
Cut: 8 lines gone. Baaki sab kuch usi jagah hai jahan tha, sirf ek bhi beat nahi gaya.

Third person. Ek ghar, teen sau card, aur paanch naam jo poore nahi hote.
**Koi rasm nahi, koi mulk nahi** — Karachi, Delhi, Dhaka, Dubai, Southall: ek hi film.
**Fiction hai. Aapki zindagi ka koi waqia isme nahi.**

---

## SCRIPT

```
Teen sau card.

Beta ko paanch naam chahiye the, un logon ke jo sach me apne hain.

Abbu ke paas teen sau card the, aur naam ek bhi nahi tha.

Beta ne poocha.

Kis ka naam likhun?

Abbu ne kaha ke log hain, aur logon ke naam nahi hote.

Abbu hanse, phir pencil uthai, aur woh teen sau card ke upar hawa me ruk gayi.

Ek naam.

Do naam kaaghaz pe aaye, teesra aaya hi nahi, kyunki teesre naam ke saath ek purani ladaai yaad aa gayi, aur pencil neeche rakh di gayi.

Raat bhar beta chup baitha, aur subah Abbu ne kaha ke sau log aayenge, aur sau plate lagengi.

Beta ne poocha ke jab tum bimaar the, tab kaun aaya tha, kaun plate laya tha?

Abbu ne jawab nahi diya, lekin unki ungli card ki ginti par wapas chali gayi.

Phir aakhri lifafa uthaya.

Us pe likha tha, log nahi.

Woh lifafa baaki lifafon ke neeche chala gaya, us almari me, jahan koi kabhi nahi dekhta.

Teen sau card, sau plate, aur ek aadmi ke paas paanch naam nahi.

Jinke naam tum nahi le sakte, unke naam pe apni zindagi nahi de sakte.
```

---

## Chaar gate — chaar green

| gate | score |
|---|---|
| `script_qc.py --tier viral` | **100/100** |
| `storygate.py` | **100/100 STORY** |
| `humanize_ur.py` | 94/100 · voice drift **0 of 6** |
| `noslop_ur.py` | **PASS** · 0 hard |

**Viral DNA:** 11.5 words/sentence · 2 sawaal · 3 words hook · third person.

---

## Kya badla, aur kyun (v5 → v6)

1. **62 s → 55 s.** 222 → 195 words. Har line jaanch kar rakhi: "Beta ne dekha", "Teen sau card the, aur paanch naam poore nahi hue", "Sirf paanch", "Subah Abbu ne kaha…" — jo dobara keh raha tha, gaya.
2. **Ek sawaal do tukdon me toota:** `Beta ne poocha.` / `Kis ka naam likhun?` — do chhote vaar, ek lamba sawaal nahi. Isse film ki saans tez hui aur aapki asli voice (chhote bursts) match hui.
3. **Pencil ab sirf hawa me nahi rukti** — woh **teen sau card ke upar** rukti hai. Image ko object mil gaya. Yahi film ka poster frame hai.
4. **"kaun plate laya tha?"** — "kaun aaya tha" ka jawab Abbu ke paas nahi, isliye sawaal plate tak le jaana pada. Jo aadmi naam nahi le sakta, woh **ginti** kar sakta hai.
5. Kuch nahi hataya — kuch **tight** kiya. Baap ka jhagda, raat, subah ki ginti, ungli, lifafa, almari: sab apni jagah.

---

## Emotion engine

| beat | engine | share rate |
|---|---|---|
| pencil teen sau card ke upar rukti hai | **AWE** | 5.3× |
| "log hain, aur logon ke naam nahi hote" | **ANGER** — dhaal ka parda khula | 4.8× |
| "jab tum bimaar the, kaun plate laya tha?" | **ANGER peak** | 4.8× |
| lifafa almari me | **ANXIETY** | 3.7× |
| sadness | **use nahi kiya** | 0.7× — reject |

---

## Beats · 55.0 s

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.0 | teen sau card, rassi se bandhe. `TEEN SAU CARD.` |
| 2 | 2.0–5.7 | beta darwaze me, card uske pairon ke aas paas |
| 3 | 5.7–9.1 | Abbu, register, chashma, khaali jagah jahan naam aane the |
| 4 | 9.1–11.2 | **do chhote shot:** `Beta ne poocha.` / `Kis ka naam likhun?` |
| 5 | 11.2–14.0 | sirf Abbu ka moonh — `log hain, aur logon ke naam nahi hote` |
| 6 | 14.0–18.8 | pencil uthti hai, **card ke upar hawa me rukti hai**. 3 s sirf graphite |
| 7 | 18.8–19.6 | `Ek naam.` — ek harf |
| 8 | 19.6–25.8 | do naam. teesre pe haath kaanpta hai. pencil neeche |
| 9 | 25.8–30.9 | raat → subah. `sau log aayenge, sau plate lagengi` |
| 10 | 30.9–35.0 | `jab tum bimaar the, kaun aaya tha, kaun plate laya tha?` |
| 11 | 35.0–39.0 | **ungli card ki ginti par wapas** — yeh jawab hai |
| 12 | 39.0–42.5 | aakhri lifafa. `Us pe likha tha, log nahi.` **[POP] 42.0** |
| 13 | 42.5–43.3 | 800 ms — poori khamoshi, black |
| 14 | 43.3–47.0 | lifafa baaki lifafon ke neeche, almari, andhera |
| 15 | 47.0–50.5 | `Teen sau card, sau plate, aur ek aadmi ke paas paanch naam nahi.` |
| 16 | 50.5–54.2 | moral, sookha, almari ke band darwaze pe |
| 17 | 54.2–55.0 | hold. kuch nahi |

**Sound:** card ki sarsarahat · pencil ki khisk · ungli kaaghaz par · ek low sub jab ginti shuru
hoti hai · **balloon pop 42.0** · 800 ms khaali · moral ke baad kuch nahi.
**Music zero.**

---

## Trend container

`NAAM LO` — har episode: ek kaam, ek ghar, ek sawaal.
jinke liye tum chup rehte ho · jinke liye abhi bhi us ghar me ho · jinke liye roz marte ho aur woh
tumhe jaante nahi.
Ek shape. Infinite episodes. Ek brand: **TABAHI**.
