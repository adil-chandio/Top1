# Monarch Studio · Project 002

## The Light With No Battery — worked 50-second sample

**Result:** a 50.00-second 9:16 3D film, not a video-generation prompt pretending to be a render. Project 002 lives at `/monarch-studio/reflector/`. The free builder's preset is a separately editable **45-second** version for other topics; this worked example is the finished **50-second** cut.

**Question:** why does a bicycle reflector glow only when light reaches it from the right direction?

**Answer:** tiny corner cubes can return the incident light toward the source. It isn't self-powered.

### Roman Urdu voice script

| Cue | Narration |
|---:|:---|
| 00.08 | Ye light jalti dikhti hai. Lekin is mein battery hi nahi. |
| 04.05 | Ye cycle ka reflector hai. Headlight padi, toh laal chamak uthi. |
| 08.83 | Ab zara side se dekho. Headlight wohi hai, chamak kam ho gayi. |
| 14.01 | Aam aaine par tirchhi kiran pade, toh doosri taraf nikal jaati hai. |
| 19.55 | Is plastic ke peechhe chhote kone hain. Har kone ki teen satahein hain, ek doosre se nabbe degree par. |
| 27.22 | Kiran andar gayi. Pehli satah se takraayi, phir doosri, phir teesri. Ab rukh bilkul ulta. |
| 35.38 | Thori si hat kar bhi, kiran headlight ki taraf laut ti hai. Isliye driver ko zyada chamak dikhti hai. |
| 44.48 | Isne roshni banayi hi nahi. Jo mili, bas wohi wapas kar di. |

### Shot plan: exactly 1,200 frames at 24 fps

Time ranges are half-open (first frame included, next shot begins at the end); frame ranges are inclusive and zero-based.

| # | Time (s) | Frames | Purpose | Camera/action |
|---:|:---|:---|:---|:---|
| 01 | 00.00–01.50 | 0–35 | A red light with no battery | Tight on the facets. A headlight comes on, building the hot edge of the red return. |
| 02 | 01.50–04.04 | 36–96 | The sealed plastic body | Angle across the sealed lens and housing. Show plastic, not a glowing bulb. |
| 03 | 04.04–06.25 | 97–149 | Reveal the rear reflector | Widen to the saddle, rear tire, spokes and mounting bracket; establish scale. |
| 04 | 06.25–08.75 | 150–209 | Headlight lands on the reflector | Follow the headlight as it lands on the back of the stationary bike. |
| 05 | 08.75–11.67 | 210–279 | Same lamp, different viewpoint | Dolly sideways away from the source axis. Keep lamp output unchanged. |
| 06 | 11.67–13.88 | 280–332 | The side view stays dim | Overhead: the beam still connects the lamp and bike, but the lens is dim from here. |
| 07 | 13.88–16.46 | 333–394 | Set up the comparison | Set up an oblique beam on a normal flat mirror. |
| 08 | 16.46–19.46 | 395–466 | The mirror sends the ray away | Hold the different outgoing angle; highlight a single reflection. |
| 09 | 19.46–22.13 | 467–530 | Exploded lens, gasket, backing | Slide the housing, gasket and red lens apart to reveal how they fit. |
| 10 | 22.13–24.38 | 531–584 | Macro pass over the microprisms | Skim across a repeating pattern of red molded corner cells. |
| 11 | 24.38–27.17 | 585–651 | Isolate one corner cube | Scale up one cell on the bench. Mark three pairwise perpendicular back faces. |
| 12 | 27.17–29.38 | 652–704 | The ray enters the plastic | The representative ray crosses the flat front aperture and bends into the plastic. |
| 13 | 29.38–32.17 | 705–771 | Three contacts reverse three axes | Contacts light one face at a time at 29.56, 30.86, and 31.83 s. |
| 14 | 32.17–35.33 | 772–847 | The ray leaves toward the source | The ray leaves the front of the prism; it is not sent through the backing. |
| 15 | 35.33–38.75 | 848–929 | Parallel paths, opposite directions | Orthographic camera, two direction arrows: parallel but reversed, with a lateral offset. |
| 16 | 38.75–42.13 | 930–1010 | See it from the driver side | Cut back near the headlight and the red return appears bright again. |
| 17 | 42.13–45.67 | 1011–1095 | The reflector cannot light itself | Hold an overhead view. Switch the lamp off at 42.87 s; the bright return vanishes. |
| 18 | 45.67–50.00 | 1096–1199 | The final reflection | Return to the opposing view. At 46.76 s the source comes back; finish on a clean red glint. |

### Copyable production prompt

> Write a 50-second, Roman Urdu, 9:16 explainer about why a bicycle reflector glows with no battery. Open on the glint, not a title. Establish the bike, then move the viewpoint while keeping the headlight on. Show a flat-mirror control before moving inside the molded prism array. Use one enlarged corner with three perpendicular back faces, and build the ray one contact at a time. In a diagram view, show the outgoing ray parallel to the incoming one, in the opposite direction and offset. Return to the bicycle and switch the lamp off in the same shot, then restore it. Return a timed VO, short in-place captions, a camera and lighting plan, a sound cue at each causal moment, and a final accuracy check. Don't promise that all ray angles return or that this is a measured road visibility test. Label enlarged parts and slow ray graphics as visualization. Do not copy a reference clip's shots, assets, branding, wording, or sound.

### What made it into the cut

- **Picture:** original Three.js road, bike, reflector, and optical bench. Tires/spokes and lens facets are modelled. Rounded edges and separate housing/gasket/lens get their form from cool rim and warm key lights. A macro compositor controls focus; the explanatory lab segments use deep focus. The focus shift from bike to lens to an enlarged corner is the story's scale change.
- **Optics:** a plastic index of 1.49 gives a modeled critical angle of 42.16°. The selected in-prism ray strikes the three back faces at 50.54°, 54.43°, and 59.50° from their normals, above the critical angle. Each reflection reverses one component of the internal ray. Entry and exit refraction are solved at the front face. The outward unit vector's dot product with the incident one is −1 (to numerical precision); the aperture points differ. Other entry points/angles can leak or miss a face. The beam, glow width and time expansion are illustrative, not empirical photometry or a road-safety simulation.
- **Sound and text:** selected Arena Urdu voice, edited locally as eight takes; 21 short Roman Urdu phrases with word emphasis. Separate procedural stereo air, lamp cues, and three dry contact sounds share event times with the render. Leave a pause at the lamp-off beat so the picture demonstrates the difference before the last line.
- **Research:** [read the source audit](./reflector-reference-audit.md) for the Dailymotion frame windows that informed the edit. The research frames are not in the film or site.

### Check before delivering a version of your own

1. Can you identify the lens in the first second and the bicycle by the first wide shot?
2. Does the visible change in brightness during the side move happen without turning the lamp off?
3. Can you follow all three contacts, then distinguish the white input direction from the coral return direction?
4. Do the captions avoid the reflector, beam, and contact points? Can you read them on a narrow screen?
5. Do the picture and sound start on tap, seek correctly, finish at 50.00 s, and open from a saved MP4 without the website?

[Ansys: Corner-cube retroreflectors](https://optics.ansys.com/hc/en-us/articles/43071088719763-How-to-model-corner-cube-retroreflectors) · [William Beaty: bicycle reflector optics](https://www.madsci.org/posts/archives/dec2000/977675178.Es.r.html)
