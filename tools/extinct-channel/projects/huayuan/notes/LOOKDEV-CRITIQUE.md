# Environmental lookdev 1 — FAILED

The hero creature is the same generic asset from earlier rejected attempts. It is small in a mostly empty picture, with near-identical side-on coverage across the sheet. The ground is saturated artificial green; the downloaded rock surfaces render nearly black, the branching bodies read as primitive sticks, the upper half is almost empty. This is neither an acceptable ocean nor a finished scene. There is no crisis, fossil, burial, evidence or sound work in this prototype. Full-motion viewing and hearing have not occurred. It would be misleading to call it cinematic final.

Suspected technical contribution: the SDK optical shader squares its input while the target likely receives linear output. Need explicitly test the scene target color space and lighting rather than claim that bright exposure creates HDR. The cause is a hypothesis until a comparison is made.

# Environmental lookdev 2 — FAILED

Scene target color-space setting, less green ground and closer/overhead cameras improved the animal's size and produced a different silhouette at frame 700. However the image still uses the same Anomalocaris model and scene, the seabed remains a speckled plane, rocks appear as shiny black patches, branching bodies look like sticks and there is no believable underwater depth, species diversity, character interaction or motivated action. These remain the same category of flaw the user rejected. The sRGB render-target experiment did not establish a calibrated linear/HDR pipeline; it must not be called HDR verification. This remains a single-scene lookdev, not a 60-second production. Do not full-render or deliver it as the film.
