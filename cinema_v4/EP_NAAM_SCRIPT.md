# "NAAM LO" · EP script · 62 s · 222 words

**Format:** third person. Ek ghar, ek shaadi, teen sau card, aur paanch naam jo poore nahi hote.
**Desi audience, world craft.** Koi Pakistan-specific rasm nahi — sirf card, lifafa, plate, pencil.
Yeh film Karachi, Delhi, Dhaka, Dubai aur Southall me **bilkul ek jaisi** padhi jaati hai.

**Kisi cheez ka dawa nahi kiya** — yeh fiction hai. Aapki zindagi ka koi waqia isme nahi hai.

---

## SCRIPT

```
Teen sau card.

Beta ko paanch naam chahiye the, un logon ke jo sach me apne hain.

Abbu ke paas teen sau card the, aur naam ek bhi nahi tha.

Beta ne poocha ke in card pe kis ka naam likhun?

Sirf paanch.

Abbu ne kaha ke log hain, aur logon ke naam nahi hote.

Abbu hanse, phir pencil uthai, aur pencil hawa me ruk gayi.

Ek naam.

Do naam aaye, teesra aaya hi nahi, kyunki teesre naam ke saath ek purani ladaai yaad aa gayi.

Teen sau card the, aur paanch naam poore nahi hue.

Beta raat bhar chup baitha raha, aur card ki ginti karta raha.

Subah Abbu ne kaha ke sau log aayenge, aur khane ki ginti bhi sau hai.

Beta ne poocha ke jab tum bimaar the, tab kaun aaya tha?

Abbu ne jawab nahi diya, lekin unki ungli card ki ginti par wapas chali gayi.

Phir unhone aakhri lifafa uthaya, aur us pe do lafz likhe.

Beta ne dekha.

Us lifafe pe likha tha, log nahi.

Aur woh lifafa baaki lifafon ke neeche chala gaya, us almari me, jahan kisi ko nazar nahi aata aur koi kabhi nahi dekhta.

Teen sau card, sau plate, aur ek aadmi ke paas paanch naam nahi.

Jinke naam tum nahi le sakte, unke naam pe tum apni zindagi nahi de sakte.
```

---

## Chaar gate — chaar green

| gate | score |
|---|---|
| `script_qc.py --tier viral` | **100/100** |
| `storygate.py` | **100/100 STORY** |
| `humanize_ur.py` | 94/100, voice drift **0 of 6** |
| `noslop_ur.py` | **PASS**, 0 hard |

**Viral DNA:** 11.1 words/sentence (long-tail 10.2 · 1M+ 14.0) · 2 sawaal · third person.

---

## Do faisle jo maine liye, aur kyun

**1. Third person, "tu" nahi.** v6/v7/v8 me "tu" tha aur woh **lecture** ban jaati thi.
Yahan sab kuch ek ghar ke andar hai, aur "tum" sirf **aakhri line** me aata hai. Isliye film
viewer ko dosh nahi deti, **uska hisaab** dikhati hai. (you/I metric: third person, so it can't
become the 2.4× you-heavy long-tail pattern.)

**2. 11 words/sentence — compromise, not accident.**
Mega-viral English shorts 14.0 pe hain. Aapki asli likhai 8.2 pe hai. Main **11** pe rakha:
aapki saans se upar, viral band ke andar. Isse fragment-stacking khatam ho gaya jo 0.7× wali
sadness bana raha tha.

**Ek galti jo maine theek ki:** ab tak main aapki **condensed cut** ko "voice" maan ke match kar raha
tha — meri hi banayi hui 42-second trim. Aapke asli paragraphs lambe hain (`"Aur yeh duniya kitni
khubsurat hai na… koi bhookh se mar jaata hai, apnon se madad maang maang kar thak jaata hai"`).
Naya voice sample `VOICE_TU_FULL.txt` hai — Cut A **aur** Cut B. Drift isi se naapa gaya.

---

## Emotion engine

| beat | engine | rate |
|---|---|---|
| pencil hawa me rukna | **AWE** — teen sau card, aur shunya naam | 5.3× |
| "log hain, aur logon ke naam nahi hote" | **ANGER** — dhaal ka parda faash | 4.8× |
| "jab tum bimaar the, tab kaun aaya tha?" | **ANGER** peak — jawab dene ke bajaye ungli ginti pe | 4.8× |
| lifafa almari me | **ANXIETY** — koi kabhi nahi dekhega | 3.7× |
| **sadness** | use **nahi** kiya. Film rone ke liye nahi kehti. | 0.7× rejected |

---

## Beats · 62.0 s

| B | in–out | picture |
|---|---|---|
| 1 | 0.0–2.2 | teen sau card, rassi se bandhe, farsh pe. Frame 0 text: `TEEN SAU CARD.` |
| 2 | 2.2–6.0 | beta darwaze me. Card uske pairon ke aas paas |
| 3 | 6.0–9.5 | Abbu, register, chashma, aur khaali jagah jahan naam aane the |
| 4 | 9.5–12.8 | beta poochta hai. Abbu ki nazar us pe nahi |
| 5 | 12.8–14.2 | `Sirf paanch.` — 14 frame kuch nahi |
| 6 | 14.2–18.0 | sirf Abbu ka moonh: `log hain, aur logon ke naam nahi hote` |
| 7 | 18.0–21.5 | pencil uthti hai aur **hawa me ruk jaati hai**. 2.5s sirf graphite |
| 8 | 21.5–23.0 | `Ek naam.` — ek harf kaaghaz pe |
| 9 | 23.0–28.5 | do naam, phir haath kaanpta hai, pencil neeche |
| 10 | 28.5–31.5 | insert: kaaghaz pe sirf do naam, aur teen sau khaali lines |
| 11 | 31.5–37.0 | raat. beta baitha. Abbu ginta hai. Koi dialogue nahi |
| 12 | 37.0–41.0 | subah: `sau log aayenge, aur khane ki ginti bhi sau hai` |
| 13 | 41.0–45.0 | `jab tum bimaar the, tab kaun aaya tha?` — Abbu ka moonh band |
| 14 | 45.0–49.0 | **unki ungli card ki ginti par wapas** — yeh jawab hai |
| 15 | 49.0–52.0 | aakhri lifafa. do lafz |
| 16 | 52.0–53.4 | `Beta ne dekha.` |
| 17 | 53.4–56.0 | `Us lifafe pe likha tha, log nahi.` **[BALLOON POP]** 54.2 |
| 18 | 56.0–56.8 | 800 ms — poori khamoshi, black |
| 19 | 56.8–59.5 | lifafa baaki lifafon ke neeche, almari me, andhera |
| 20 | 59.5–62.0 | moral, sookha, almari ke band darwaze pe |

**Sound** card ki sarsarahat · pencil ki khisk · ungli kaaghaz par · ek low sub jab ginti shuru
hoti hai · **pop** 54.2 · 800 ms kuch nahi · moral khaali kamre me.
**Music zero.** Yeh film chup reh kar gussa karti hai.

---

## Trend container

`NAAM LO` — har episode ek kaam, ek ghar, ek sawaal:
jinke liye tum chup rehte ho · jinke liye abhi bhi us ghar me ho · jinke liye roz marte ho aur woh
tumhe jaante nahi. Ek shape, infinite episodes, ek brand: **TABAHI**.
