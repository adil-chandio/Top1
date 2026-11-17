# Batch 2 shuru: seat-belt candidate ka science/feasibility gate

**Haalat:** primary-document reading shuru ho chuki hai. Model-specific mechanism, asset inspection aur hardest-visual gate abhi complete nahin. Is document ko production approval ya finished test nahin samajhna.

## Scope correction jo sources se nikli
Candidate ka working question: 'Belt aahista kheenchne par nikalti hai, achanak pull par lock kaise hoti hai?' Isay **webbing-sensitive retractor ke ek documented example** tak limit karna hoga. Har seat belt ko isi ek sensor se chalne wala kehna ghalat hoga: NHTSA ka historical interpretation vehicle-sensitive, webbing-sensitive aur dual-sensitive distinctions explicitly discuss karta hai. Yeh 1981 interpretation hai, current worldwide certification specification nahin. [1](https://www.nhtsa.gov/interpretations/nht81-114)

## Claim ledger
| Proposed claim | Evidence/status | Allowed treatment / avoid |
|---|---|---|
| Retractors mein sensing arrangement different ho sakta hai | NHTSA historical primary interpretation mein vehicle/webbing/dual distinctions | On-screen 'webbing-sensitive example'; 'har gaari' nahin [1](https://www.nhtsa.gov/interpretations/nht81-114) |
| Relative inertia-disc lag pawl engagement actuate kar sakta hai | EP0972684A1 description says inertia disc lags reel, cam actuates pawl into frame teeth; one concrete documented design family | Source-specific schematic; lag ko free-floating magic latch nahin banana [2](https://patents.google.com/patent/EP0972684A1/en) |
| Locking path mein pawl/teeth engage hote hain | Same patent explanation; pawl mounting/support and synchronization issues more complex than generic cartoon | Tooth tip/clamp geometry aur load path visually coherent chahiye; just belt suddenly freezing kafi nahin [2](https://patents.google.com/patent/EP0972684A1/en) |
| Webbing pull test = official retractor acceleration test | **Rejected**: NHTSA interpretation specifically says retractor and webbing acceleration tests not equivalent because inertial forces differ | G values/test protocols ko home-pull demonstration ke saath equate nahin karna [1](https://www.nhtsa.gov/interpretations/nht81-114) |
| One exact speed/G threshold applies to every belt | Not established | Final script mein numeric threshold omit until exact mechanism/current source supports it |
| Lock means zero extension/no force-limiting in all crashes | Not established; current review has not validated pretensioners/load limiters | No crash-performance guarantee, no repair/disable/home-test instruction |

## Primary pages actually read
1. https://www.nhtsa.gov/interpretations/nht81-114 — fetched/read interpretation text; historical date and correction of earlier interpretation noted.
2. https://patents.google.com/patent/EP0972684A1/en — fetched/read first description chunk, includes prior design/inertia-disc/cam/pawl/frame teeth and tooth synchronization discussion. **Remaining chunks and engineering drawing visual inspection pending.** Search snippets alone not a full patent review.

Search leads not promoted to validated script facts: US7568649B2 vehicle-sensitive ball/pendulum; US20030111571A1 inertia-disc/pawl discussion. One source's geometry ko doosre source ke mechanism ke saath silently combine nahin karna.

## Hardest visual test — actual environment attempt, not passed
- Local isolated runtime mein `bpy==4.2.0` + Pillow install kiya, taake scarce Actions render slots par depend na rehna pade.
- Actual `import bpy` attempt failed: `ImportError: libXrender.so.1: cannot open shared object file`.
- `ldd` ne additional missing runtime libraries confirm ki: libXxf86vm, libXfixes, libXi, libxkbcommon, libSM, libICE, libGL.
- **No render generated, no articulated lock animation inspected, no hardest-visual approval.** Dependency installation ko animation execution nahin gina.
- Required eventual test: reel movement → documented relative lag → cam/pawl movement → tooth engagement → coherent reel stop; consecutive frames near contact must show no tooth penetration/floating anchor. Intended original procedural geometry, not copied reference footage. Until this passes, candidate A remains provisional.

## Asset / license gate
Reference media sirf analysis ke liye, production footage nahin. Public archive access aur expired-looking patent status ko artwork reuse/license clearance nahin maana. Koi licensed production model/texture inspect/acquire abhi nahin hua. Procedural original geometry/lighting ka route available ho sakta hai, lekin abhi built/approved claim nahin.

## Next-candidate rule
A ka bounded contact/rig test fail/unresolved rahe to candidate C (soap pump) ka source-specific test next, endless cosmetic polish nahin. Abhi A ko technically infeasible globally declare nahin kiya: current missing-libraries failure environment ka hai, mechanism animation ki impossibility ka saboot nahin.

Dependency recovery ka actual attempt: `sudo -n apt-get install` required eight libraries ke liye chalaya; package lists mein packages available nahin the (`Unable to locate package`). Is attempt se runtime fix nahin hua. Downloaded Python dependencies ignored `studio/runtime/` mein hain, Git artifacts nahin.
