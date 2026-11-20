"""Close granular Foley, a scored constriction, and the locked opening VO.

Picture events are authored in absolute native-frame coordinates. Fractions of
frames represent only sound layers within one audible event, never VO edits.
"""
import json
from math import pi

from pilot import CONTACT, FPS, LANDING, QA, SAMPLES, SR, WORK, make_dirs, voice_plate
from mix import Bus, apply_envelope, band, db, envelope, excerpt, gain, measure, ns, peak_duck, play, rms, rms_blocks, wav
import numpy as np

# Frame, event, recording, duration, pitch/speed, low/high rolloffs, RMS level,
# near-field pan, attack, recording-offset seed. Three layers make ONE strike.
SPOTS = [
    (3.1, 'front tarsus catches grain', 'sand-step', .135, 1.16, 171, 2930, -36.5, -.28, .004, 0),
    (20, 'toe searches', 'gravel_02', .117, 1.15, 196, 2850, -41, .19, .006, 1),
    (40, 'tarsus slips', 'sand-step-alt', .178, 1.19, 166, 2480, -39, -.11, .011, 0),
    (47, 'sand starts before cut', 'sand-sweep', .72, .94, 159, 2870, -41, .20, .057, 3),
    (67, 'stone and suspended grains', 'gravel_07', .254, .92, 137, 2300, -45, .21, .017, 0),
    (91.7, 'sand slips under COMING', 'sand-sweep', .81, 1.12, 189, 2960, -39.8, -.16, .074, 1),
    (102, 'DOWN settles', 'gravel_08', .166, 1.06, 173, 2280, -42.3, -.34, .013, 0),
    (126.3, 'rear foot finding purchase', 'sand-step-alt', .181, .94, 198, 3140, -38.1, -.27, .006, 1),
    (146, 'second toe on rock side', 'sand-step', .146, 1.15, 225, 3080, -41.8, .14, .006, 1),
    (165, 'grip shears', 'sand-sweep', 1.19, .83, 185, 2670, -39.7, -.08, .116, 0),
    (183, 'heel skid', 'gravel_05', .213, 1.06, 157, 3010, -40.9, -.24, .009, 0),
    (198, 'witness grain first tumble', 'gravel_07', .218, 1.29, 259, 3650, -39.7, .30, .010, 1),
    (209, 'witness grain taps ridge', 'gravel_02', .132, 1.31, 293, 3680, -41, .02, .005, 0),
    (221, 'witness grain accelerates', 'gravel_08', .217, 1.43, 291, 3070, -43.7, -.25, .007, 0),
    (227.2, 'pincer air brushes lens', 'sand-sweep', .49, 1.45, 128, 2130, -39, -.37, .071, 1),
    (268.7, 'larva head flick / close grit', 'gravel_05', .247, .96, 169, 3450, -36.9, -.12, .006, 0),
    (271.0, 'larva sand cast', 'sand-sweep', .69, 1.13, 221, 3210, -39.0, .29, .038, 2),
    (293, 'cast falls back', 'gravel_08', .285, .82, 160, 2440, -42.2, .22, .016, 0),
    (312, 'fallen sand / across head cut', 'sand-sweep', .94, .86, 149, 2430, -43.2, -.04, .141, 3),
    (343, 'last tarsus finds sand', 'sand-step', .158, .91, 172, 2550, -40.2, .17, .006, 1),
    (383.9, 'stance settles', 'gravel_07', .225, .80, 152, 1990, -44.3, -.09, .016, 0),
    (400.8, 'small jaw aim movement', 'sand-step-alt', .145, 1.19, 226, 2180, -46.1, .34, .013, 0),
    (CONTACT, 'jaw-sand / one dry snap', 'soft-snap', .106, 1.04, 153, 3330, -30.2, .25, .0016, 0),
    (CONTACT+.34, 'jaw-sand / buried grains', 'sand-step', .251, 1.14, 201, 3190, -36.6, .27, .008, 1),
    (CONTACT+1.18, 'jaw-sand / debris', 'sand-sweep', .655, 1.21, 191, 3310, -39.0, .23, .033, 3),
    (CONTACT+7.8, 'ejected grit separates', 'gravel_08', .217, 1.06, 222, 2830, -40.7, .38, .011, 0),
    (480.0, 'air travels with cut to wide', 'sand-sweep', .621, 1.21, 82, 1410, -44.2, -.38, .131, 2),
    (LANDING, 'rim landing / distant sand', 'sand-step-alt', .250, .86, 143, 2640, -36.0, -.46, .004, 0),
    (LANDING+1.0, 'rim landing / grit tail', 'gravel_02', .232, .89, 221, 2460, -42.3, -.43, .012, 0),
    (552.8, 'study rotation light texture', 'sand-sweep', .52, 1.4, 201, 2510, -46.3, .33, .135, 0),
    (574.4, 'light diagram detent, not another strike', 'snap-alt', .072, 1.27, 590, 2490, -46.9, .26, .007, 1),
    (597.8, 'last close step', 'sand-step', .148, .97, 192, 2810, -41, -.14, .006, 0),
    (624.0, 'foot crosses small grains', 'gravel_07', .188, 1.13, 154, 2660, -42.2, .06, .011, 0),
    (648.5, 'rim move', 'gravel_05', .139, .91, 174, 2600, -43, .17, .006, 1),
    (670.5, 'breath across overhead cut', 'sand-sweep', 1.24, .87, 154, 1660, -44.4, -.20, .164, 1),
]

# frame, instrument, pitch, duration, level, pan. The same falling interval in
# the slip becomes a rising response after the lift. No start-of-shot music hit.
SCORE = [
    (31, 'cello', 'D3', 4.40, -37.5, -.29),
    (71, 'piano', 'A3', 2.75, -35.2, .18),
    (103, 'pizz', 'F3', .73, -39.6, -.35),
    (147, 'cello', 'Bb2', 3.20, -37.2, -.30),
    (167, 'piano', 'F3', 2.13, -37.0, -.12),
    (201, 'pizz', 'D3', .77, -37.8, .25),
    (247, 'cello', 'A2', 4.28, -37.1, -.34),
    (273.5, 'cello', 'Eb3', 3.31, -39.1, .27),
    (304, 'piano', 'A3', 2.84, -36.1, .23),
    (351, 'cello', 'E3', 2.04, -38.3, -.17),
    (447, 'cello', 'D3', 4.02, -36.6, -.31),
    (461, 'piano', 'F4', 2.98, -33.9, -.12),
    (482, 'piano', 'A4', 2.43, -36.0, .23),
    (490, 'cello', 'A3', 3.11, -38.8, .36),
    (529, 'piano', 'F4', 2.47, -40.2, -.11),
    (557, 'pizz', 'D4', .78, -40.1, .27),
    (598, 'cello', 'F3', 3.29, -39.1, -.38),
    (636, 'piano', 'E4', 2.27, -39.3, .14),
    (669, 'piano', 'A4', 1.5, -38.0, .23),
]
INST = {'piano': 'acoustic_grand_piano', 'pizz': 'pizzicato_strings', 'cello': 'cello'}


def synth_hit():
    t = np.arange(ns(.156), dtype=np.float32) / SR
    return envelope((np.sin(2*pi*(143*t-151*t*t))*np.exp(-t*38)).astype(np.float32), .008, .03)


def build():
    make_dirs()
    voice, placement = voice_plate()
    foley, score = Bus(SAMPLES), Bus(SAMPLES)
    spots = []
    for frame, label, src, d, speed, lo, hi, level, pan, attack, seed in SPOTS:
        start = round(frame * (SR // FPS))
        x = excerpt(src, d, speed, lo, hi, seed, attack=attack, release=min(.18, d*.51))
        first = len(x) if 'sweep' not in src else min(ns(.44), len(x))
        cap = .185 if frame == CONTACT else .116
        amp = min(gain(level) / max(rms(x[:first]), 1e-6), cap/(np.max(np.abs(x))+1e-6))
        foley.add(x, start/SR, amp, pan)
        spots.append(dict(frame=frame, sample=start, cue=label, source=src, length_s=d, pan=pan, speed=speed,
                          level_dBFS=round(db(amp*rms(x[:first])),2)))
    foley.add(synth_hit(), (CONTACT+.19)/FPS, .023, .10)
    spots.append(dict(frame=CONTACT+.19, sample=round((CONTACT+.19)*SR/FPS),
                      cue='jaw-sand / damped low body, part of same snap', source='original synthesis'))
    for frame, instr, midi, duration, level, pan in SCORE:
        play(score, INST[instr], midi, frame/FPS, duration, level, pan, 1.)

    # L-cut debris under the camera change; short pre-impact subtraction is
    # distinct from the broader, gentle speech-aware attenuation on each bus.
    duck = peak_duck(voice)
    t = np.arange(len(duck)) * .02 * FPS
    arc = np.interp(t, [0, 200, 228, 242, 282, 377, 410, 436, 444, 465, 513, 536, 660, 705],
                       [.94, .95, .36, .31, 1., .92, .42, .053, .072, 1., 1., .86, .93, .80])
    tick = np.interp(t, [0, 377, 402, 417, 438, 441, 445, 485, 507, 543, 687],
                        [1., 1., .69, .58, .64, 1., 1., .83, .88, .94, 1.])
    apply_envelope(score.y, arc*(1-.65*duck), SR//50)
    apply_envelope(foley.y, tick*(1-.30*duck), SR//50)
    for bus in [score, foley]:
        fade = ns(.44)
        bus.y[-fade:] *= np.cos(np.linspace(0, pi*.5, fade, dtype=np.float32))[:,None]**2
    mix = (voice[:,None] + foley.y + score.y).astype(np.float32)
    assert np.max(np.abs(mix)) < .80 and len(mix) == SAMPLES
    wav(foley.y, WORK/'v3-foley.wav')
    wav(score.y, WORK/'v3-score.wav')
    wav(mix, WORK/'v3-mix.wav')
    m = measure(WORK/'v3-mix.wav')
    v, b = rms_blocks(voice, ns(.12)), rms_blocks(np.mean(foley.y+score.y, axis=1), ns(.12))
    good = v > gain(-37)
    under = 20*np.log10(np.maximum(b[good]/v[good], 1e-10))
    d = dict(vo_placements=placement, samples=SAMPLES, active_dialogue_bed_dB={str(i):float(np.percentile(under,i)) for i in [50,90,95,99]},
             premix=m, peak_dBFS=db(np.max(np.abs(mix))), score_cues=len(SCORE), foley_layers=len(spots))
    (QA/'mix.json').write_text(json.dumps(d, indent=2)+'\n')
    (WORK/'spotting.json').write_text(json.dumps(dict(foley=spots, score=SCORE), indent=2)+'\n')
    print(json.dumps(d,indent=2))
    assert -22 < m['LUFS_I'] < -17.8 and m['dBTP'] < -2.9, m
    assert d['active_dialogue_bed_dB']['95'] < -11.8, d
    print('V3_MIX_READY')


if __name__ == '__main__':
    build()
