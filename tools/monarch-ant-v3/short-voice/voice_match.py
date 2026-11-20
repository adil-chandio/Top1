"""Match the locked Short's narration to Monarch Cam's approved long cut.

Keep the exact picture packets, subtitle bits, words and sample clock. When
only the delivered Short is available, recover dialogue using the existing
Foley and score recipes, not a different take or a global treble cut. The
accepted dry VO measures tonal balance; the long cut sets program level.
"""
from hashlib import file_digest
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np
from scipy.signal import butter, sosfiltfilt

HERE = Path(__file__).resolve().parent
C = Path(os.environ.get('MONARCH_SHORT_VOICE_CACHE', '.cache/monarch-ant-short-voice')).resolve()
REF = C / 'reference'
OUT = Path(os.environ.get('MONARCH_SHORT_VOICE_DELIVERY', 'deliverables/monarch-cam-step-6-short-voice')).resolve()
os.environ.setdefault('MONARCH_V2_CACHE', str(C / 'bank'))
sys.path.insert(0, str(HERE.parent / 'short-foley'))
import remix as old
from remix import SAMPLES, SPF, SR, FPS, short
from mix import Bus, LEVEL, apply_envelope, db, decode, envelope, ff, gain, measure, ns, peak_duck, rms, rms_blocks, wav

SHORT = REF / old.NAME
SRT = SHORT.with_suffix('.en.srt')
LONG = REF / 'Monarch-Cam-Ant-V3-Full-Cinematic-Cut-Drive-Review.mp4'
VO = REF / 'Monarch-Cam-Ant-VO-v1.wav'
NAME = 'Monarch-Cam-01A-Bite-To-Jump-Short-Voice-Match'
LOCK = {
    SHORT: 'aea7534ffe2641645c5909bb65db37fc9637aef3dd28a5bd97ee5628c9b5d8e5',
    SRT: old.CAPTION_SHA,
    LONG: '142261a118e4b6bc13f1aa4d47e1f146976d0e29a42f0c485cdd640b581e3885',
    VO: '4a3d3c596005cee1f077cc24c0b3a8e55ae9c29614b1f4ed77d119fd5fbf5929',
}
# Verified PCM receipt from the Short Foley master. This is not used as a
# target gain; only to reproduce the existing sidechain at its input level.
FORMER_FADER = 0.91 * 1.9253070450776837


def digest(path):
    with path.open('rb') as f:
        return file_digest(f, 'sha256').hexdigest()


class Accompaniment:
    def __init__(self):
        self.foley = old.conform()
        bus = Bus(SAMPLES)
        short.score(bus)
        self.score = bus.y
        self.room = short.ground_tone() * (FORMER_FADER / .91) * gain(-1.9)
        self.fade = envelope(np.ones(SAMPLES, dtype='f'), .004, .020)

    def stems(self, voice):
        side = peak_duck(voice / FORMER_FADER, 480)
        fx, dust = self.foley.near.y.copy(), self.foley.dust.y.copy()
        apply_envelope(fx, 1. - .064 * side, 480)
        apply_envelope(dust, 1. - .34 * side, 480)
        score = self.score.copy()
        short.ride_score(score, side)
        return old.impact_focus(fx + dust), old.score_space(score * (FORMER_FADER / .91)) + self.room

    def recover(self, stereo):
        # Mid is the center narration plus some accompaniment. Side has no
        # narration, so it independently tests the reconstruction. Iterate
        # because the original bed was ducked by the original voice.
        inv = 1. / np.maximum(self.fade, .065)
        voice = stereo.mean(axis=1) * inv
        for _ in range(6):
            fx, bed = self.stems(voice)
            pred = old.limiter((voice[:, None] + fx + bed) * self.fade[:, None])
            voice += .93 * (stereo - pred).mean(axis=1) * inv
        fx, bed = self.stems(voice)
        pred = old.limiter((voice[:, None] + fx + bed) * self.fade[:, None])
        snd = stereo[:, 0] - stereo[:, 1]
        est = pred[:, 0] - pred[:, 1]
        # Report true codec/reconstruction error, not idealized nulling.
        check = dict(side_correlation=float(np.corrcoef(snd, est)[0, 1]),
                     side_error_db=db(rms(snd - est) / rms(snd)),
                     roundtrip_error_db=db(rms(stereo - pred) / rms(stereo)))
        # AAC can quantize low-level stereo differences aggressively. Also
        # require an absolute full-program null, not only a side statistic.
        assert check['side_correlation'] > .91 and check['roundtrip_error_db'] < -31., check
        return voice, fx, bed, check


BANDS = dict(body=(180, 1700), edge=(1850, 4250), ess=(4500, 9750), phone=(270, 4200))


def isolate(x, band):
    return sosfiltfilt(butter(3, band, btype='bandpass', fs=SR, output='sos'), x).astype('f')


def levels(x):
    q = {'all': rms_blocks(x, ns(.020))}
    for k, band in BANDS.items():
        q[k] = rms_blocks(isolate(x, band), ns(.020))
    return q


def spectrum_stats(xs):
    mask = xs['all'] > gain(-39.)
    # Compare active dialogue only; the long film has intentionally more rests.
    ans = {'active_windows': int(np.count_nonzero(mask))}
    for k, y in xs.items():
        ans[k] = np.round(20*np.log10(np.maximum(np.percentile(y[mask], [50, 90, 97, 99]), 1e-8)), 2).tolist()
    for a in ('edge', 'ess'):
        rel = 20*np.log10(np.maximum(xs[a], gain(-66.)) / np.maximum(xs['body'], gain(-39.)))
        ans[a+'_vs_body'] = np.round(np.percentile(rel[mask], [50, 90, 97, 99]), 2).tolist()
    return ans


def reference():
    for p, sha in LOCK.items():
        assert digest(p) == sha, f'Not the locked media: {p}'
    old.verify_bank(False)
    y = decode(SHORT, 2)
    assert SAMPLES <= len(y) < SAMPLES+1024, len(y)
    stage = Accompaniment()
    voice, fx, bed, check = stage.recover(y[:SAMPLES])
    ref = decode(VO) * LEVEL
    by_source = dict(long_mix=measure(LONG), previous_short_mix=measure(SHORT),
                     long_dialogue=spectrum_stats(levels(ref)), short_dialogue=spectrum_stats(levels(voice)),
                     recovery=check)
    print('LOCKED_AUDIO_ANALYSIS', json.dumps(by_source, indent=2), flush=True)
    return voice, fx, bed, stage.fade, by_source


def rms_track(x, hop=240, window=960):
    """Centered RMS for 20-ms windows every 5 ms, including the ends."""
    p = np.pad(x, (window//2, window//2))
    power = np.r_[0., np.cumsum(np.square(p, dtype='float64'))]
    centers = np.arange(0, len(x), hop)
    return centers, np.sqrt(np.maximum((power[centers+window]-power[centers])/window, 0.))


def shape_voice(voice, ref_stats):
    # Satisfy the matched-level comparison without touching the original
    # rhythm, pitch, words or breath intervals. Undo the earlier +1.5 dB
    # presence push; reserve dynamic attenuation for sharp speech windows.
    v = (voice * gain(-3.35)).astype('f')
    v += (gain(-1.65) - 1.) * isolate(v, BANDS['edge'])
    report = {}
    for key, cap, slope, margin in [('edge', 3.65, .60, 1.1), ('ess', 5.2, .64, .7)]:
        part = isolate(v, BANDS[key])
        t, p = rms_track(part)
        _, b = rms_track(isolate(v, BANDS['body']))
        level = 20*np.log10(np.maximum(p, gain(-90.)))
        ratio = level - 20*np.log10(np.maximum(b, gain(-39.)))
        x = np.maximum((ratio - ref_stats[key+'_vs_body'][1] + margin)*slope,
                       .45*(level - ref_stats[key][1] + .8))
        # Don't clamp normal quiet diction just because it follows a vowel;
        # apply reduction only when this band has appreciable energy.
        reduction = np.clip(x, 0., cap)*np.clip((level - ref_stats[key][1]+15.)/11., 0., 1.)
        # Small anticipatory ride catches the consonant without a time shift.
        rel = np.maximum(reduction, np.r_[reduction[1:]*.75, 0.])
        for i in range(1, len(rel)):
            rel[i] = max(rel[i], rel[i-1]*.80)
        ride = np.interp(np.arange(len(v)), t, 10**(-rel/20)).astype('f')
        v -= (1.-ride)*part
        report[key] = dict(static_db=-1.65 if key=='edge' else 0.,
                           additional_max_db=round(float(rel.max()), 3),
                           windows_over_1db=int(np.count_nonzero(rel>1.)))
    return v, report


def softer_limit(x):
    # Peak safety only; do not press the narration back into a flat block.
    return short.processor(x, 'alimiter=limit=.630:attack=4:release=55:level=false:latency=true', 2)


def assemble():
    voice, fx, bed, fade, proof = reference()
    v, ride = shape_voice(voice, proof['long_dialogue'])
    # Keep every previous effect and spot, with comfortable headroom under
    # the new voice. Music and grain texture remain under the breaths.
    f = fx * gain(-3.60)
    b = bed * gain(-3.20)
    a = (v[:, None]+f+b)*fade[:, None]
    p = C / 'voice-match.wav'
    wav(a, p)
    premix = measure(p)
    target = proof['long_mix']['LUFS_I'] + .25
    offset = target - premix['LUFS_I']
    assert abs(offset) <= 1.6, (premix, target, offset)
    amp = gain(offset)
    a *= amp
    out = softer_limit(a)
    assert out.shape == (SAMPLES, 2) and rms(out-a)/rms(a) < .018
    wav(out, p)
    v *= amp
    new_stats = spectrum_stats(levels(v))
    before = proof['short_dialogue']
    ref_stats = proof['long_dialogue']
    # Check both absolute reference level and excess over the low-mid body.
    # The upper-mid and sibilance changes cannot pass on volume alone.
    for k in ('edge', 'ess'):
        assert before[k][1]-new_stats[k][1] > 4.5, (k, before[k], new_stats[k])
        assert new_stats[k+'_vs_body'][1] < before[k+'_vs_body'][1]-2.0, (k, new_stats)
        assert abs(new_stats[k][1]-ref_stats[k][1]) <= 3.2, (k, new_stats, ref_stats)
    assert abs(new_stats['body'][1]-ref_stats['body'][1]) < 2.8, (new_stats, ref_stats)
    # Protected-band likeness catches accidental retiming or aggressive
    # smoothing over words. All processing uses the original sample positions.
    c = float(np.corrcoef(isolate(v, BANDS['body']), isolate(voice, BANDS['body']))[0, 1])
    assert c > .991, c
    master = measure(p)
    assert abs(master['LUFS_I']-target)<.20 and master['dBTP']<=-3.6, master
    marks = [5, 194, 328, 439, 644, 696, 790]
    spots = {}
    for i in marks:
        q = slice(i*SPF, i*SPF+ns(.16))
        spots[str(i)] = dict(seconds=i/FPS, old_dbfs=db(rms(fx[q])), new_dbfs=db(rms(f[q])*amp))
        assert -5.3 < spots[str(i)]['new_dbfs']-spots[str(i)]['old_dbfs'] < -1.5, (i, spots)
    proof.update(new_dialogue=new_stats, dialogue_ride=ride, raw_mix=premix, makeup_db=offset,
                 master=master, protected_dialogue_corr=c, locked_effect_spots=spots)
    print('VOICE_SHAPING', json.dumps({k:proof[k] for k in ('new_dialogue','dialogue_ride','raw_mix','makeup_db','master')},indent=2),flush=True)
    return p, out, proof


def mux():
    wav_path, pcm, proof = assemble()
    mp4 = C / (NAME + '.pending.mp4')
    ff('-loglevel', 'error', '-y', '-i', SHORT, '-i', wav_path, '-map','0:v:0','-map','1:a:0',
       '-map_chapters','-1','-c:v','copy','-c:a','aac','-b:a','224k','-ar',SR,'-ac','2',
       '-metadata:s:a:0','language=eng','-video_track_timescale','30000','-movflags','+faststart+write_colr',mp4)
    h = old.hash_video(mp4)
    assert h == old.hash_video(SHORT), h
    picture = old.qc.encode_gate(mp4)
    track = decode(mp4, 2)
    assert SAMPLES <= len(track) < SAMPLES+1024, len(track)
    a = track[:SAMPLES]
    corr = float(np.corrcoef(a.ravel(), pcm.ravel())[0, 1])
    assert corr > .995, corr
    meter = measure(mp4)
    assert abs(meter['LUFS_I']-proof['long_mix']['LUFS_I']) < .60 and meter['dBTP'] <= -3.5, meter
    gap = 10*max((r-l for l,r in short.runs(rms_blocks(a.mean(axis=1), SR//100)>gain(-51), False)),default=0)
    assert gap <= 70, gap
    proof.update(reference_sha256={p.name:sha for p,sha in LOCK.items()}, picture=picture, encoded=meter,
                 frames=picture['frames'], video_packet_hash=h, audio_samples=SAMPLES, encoded_pad_samples=len(track)-SAMPLES,
                 encode_pcm_corr=corr, longest_below_floor_ms=gap, sha256=digest(mp4), size=mp4.stat().st_size)
    assert proof['size'] < 100_000_000
    OUT.mkdir(parents=True,exist_ok=True)
    for source, suffix in [(SRT,'.en.srt'), (HERE/'upload.txt','-Upload.txt'), (mp4,'.mp4')]:
        target=OUT/(NAME+suffix)
        tmp=target.with_name(target.name+'.pending')
        shutil.copyfile(source,tmp)
        tmp.replace(target)
    mp4.unlink()
    (C/'receipt.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('VOICE_MATCH_READY', OUT/(NAME+'.mp4'), meter, proof['sha256'], flush=True)


if __name__ == '__main__':
    mux()
