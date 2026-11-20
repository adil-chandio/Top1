#!/usr/bin/env python3
"""Build the long-cut VO from the named, checksum-pinned takes, not the v1 audio.

Same CPU dependencies as build_voiceover.py. --probe also runs independent ASR
as a diagnostic; captions are the approved script plus forced word alignment.
Neither the script nor any delivered v1 artifact is edited by this builder.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import re
import wave

import numpy as np
from pocketsphinx import Decoder
from scipy.signal import resample_poly

from build_voiceover import (
    HERE, ROOT, OUT, OUT_RATE, SOURCE_RATE, WORD, digest, ffmpeg, loudness, tc, timestamp,
)

SCRIPT = HERE.parent / 'step-2/Extinct-Life-Atlantic-Tracks-Script-v2.md'
LOCK = HERE / 'take-lock-v2.json'
TAKES = ROOT / '.cache/monarch-extinct/atlantic-tracks/voice-v2'
STEM = 'Extinct-Life-Atlantic-Tracks-VO-v2'
HOLD = (.44, .50, .46, .51, .50, .51, .57)
GAIN_DB = -1.30
CPS = 20.0
PHONES = {
    'koum': 'K UW M', 'sousa(2)': 'S OW Z AH', 'gondwana(2)': 'G AA N D W AA N AH',
    'mayo(2)': 'M AA Y OW', 'mayo(3)': 'M AY OW', 'mawsonia': 'M AO S OW N IY AH',
    'mawsonia(2)': 'M AO S OW N Y AH', 'theropod': 'TH EH R AH P AA D',
    'trackway': 'T R AE K W EY', 'trackways': 'T R AE K W EY Z',
    'modelled': 'M AA D AH L D', "dinosaur's": 'D AY N AH S AO R Z',
}
WEAK_END = frozenset('a an the and or in of to at from as by with on for that which this those these if its their'.split())
KEEP_TOGETHER = (
    'Mayo Rey River', 'Koum Basin', 'Sousa Basin', 'Early Cretaceous', 'six thousand kilometres',
    'a thousand kilometres', 'two hundred and eighty-three footprints', 'thirty-four trackways',
    'same ancient landmass', 'sixty-nine centimetres', 'two thousand overlapping photographs',
    '2024 reconstruction', 'mineral cement', 'microbial mats', 'called Mawsonia', 'single animal',
    'not a dinosaur', 'dry ground', 'both sides', 'old river system', 'the two places',
    'four different surfaces', 'thin mats of microbes',
)
# Give the first two pins and the closing reversal individual caption beats.
CAPTION_STARTS = ('More in Cameroon.', 'Look up the two places', 'Not a dinosaur.', 'The rocks.', 'The footprints stayed')
BEATS = (
    (1, 'Three-toed dinosaur tracks', 'First frame: schematic print and modern map. No specimen photo needed.'),
    (1, 'More in Cameroon', 'Light the distinct second pin.'),
    (1, 'six thousand kilometres', 'Show ≈6,000 km today.'),
    (1, 'But rewind the map', 'Match-cut to the 125 Ma reconstruction. Keep the model-not-fossil-date label visible.'),
    (1, 'a thousand kilometres apart', 'Show the study estimate, ≈1,000 km on connected land. No footsteps across the map.'),
    (2, 'two hundred and eighty-three footprints', 'Koum survey count. Keep prints and trackways distinct; no animal headcount.'),
    (2, "And the tracks aren't all on the same surface", 'Expose four schematic bedding surfaces separately.'),
    (2, 'two thousand overlapping photographs', 'Overlapping views → original schematic relief. Not the field team’s mesh.'),
    (3, 'Sixty-nine centimetres', 'Ruler for one ~69 cm impression; no giant body estimate or stock specimen.'),
    (3, 'Press the same three-toed shape', 'One stamp, two substrates. Show the edges hold vs. slump.'),
    (4, 'Ripples in the rock', 'Ripple marks → separate dried mud clue.'),
    (4, 'Under a microscope', 'Schematic thin section, early cement and microbial mat; not a photographed micrograph.'),
    (4, 'If fresh sediment buried', 'Show the imprint being covered, not a claim about a particular print’s exact burial.'),
    (5, 'Now cross the modern Atlantic', 'Switch to Sousa Basin, Brazil, with a distinct substrate panel.'),
    (5, 'raised rims', 'Show the displaced edge in a labelled original schematic.'),
    (6, 'fossil pollen', 'Compare regional age evidence, not an exact date on a footprint.'),
    (6, 'Then you restore the geography', 'Return to the older geography and geological structures.'),
    (6, 'As the crust stretched', 'Generic fault block → sediment-catching low area.'),
    (7, 'could have linked those habitats', 'Broad possible dispersal area, not a direction of migration.'),
    (7, "There's even a clue that didn't leave footprints", 'Fish schematic; fossils from other basins, not these slabs.'),
    (7, 'What would make the case stronger', 'Hypothetical better-dated sites; do not show newly discovered specimens.'),
    (8, 'the ocean widened', 'Return to present-day map; separation in stages, not a one-day split.'),
    (8, 'Not a dinosaur. The rocks.', 'Hold on the two distinct sites for the payoff; source credits after the last line.'),
)


def tokens(text):
    return WORD.findall(re.sub(r'\b2024\b', 'twenty twenty-four', text).lower())


def read_native(path):
    with wave.open(str(path), 'rb') as wav:
        assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (SOURCE_RATE, 1, 2)
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').astype('float32') / 32768


def decode(path, text, independent):
    native = read_native(path)
    rate16 = resample_poly(native, 160, 441)
    pcm = np.rint(np.clip(rate16, -1, 32767 / 32768) * 32768).astype('<i2').tobytes()
    d = Decoder(samprate=16000, frate=100, loglevel='ERROR')
    for n, pron in PHONES.items():
        if not d.lookup_word(n):
            d.add_word(n, pron, False)
    expected = tokens(text)
    assert not [w for w in expected if not d.lookup_word(w)]

    def run():
        d.start_utt()
        d.process_raw(pcm, full_utt=True)
        d.end_utt()

    diagnostic = None
    if independent:
        run()
        heard = d.hyp().hypstr if d.hyp() else ''
        alt = heard.split()
        diagnostic = {
            'unconstrained_hypothesis': heard,
            'diff': [[op, ' '.join(expected[i:j]), ' '.join(alt[k:l])] for op, i, j, k, l in
                     SequenceMatcher(None, expected, alt, autojunk=False).get_opcodes() if op != 'equal'],
        }
    d.set_align_text(' '.join(expected))
    run()
    spans = [{'word': re.sub(r'\(\d+\)$', '', t.word), 'variant': t.word,
              'start': t.start_frame / 100, 'end': (t.end_frame + 1) / 100}
             for t in d.seg() if not t.word.startswith(('<', '['))]
    assert [s['word'] for s in spans] == expected
    assert 0 <= spans[0]['start'] < .35 and spans[-1]['end'] <= len(native) / SOURCE_RATE
    assert len(native) / SOURCE_RATE - spans[-1]['end'] < .55
    return {'sha256': digest(path), 'text': text, 'spans': spans, 'duration': len(native) / SOURCE_RATE, 'diagnostic': diagnostic}


def align_job(job):
    idx, path, text, probe = job
    return idx, decode(path, text, probe)


def reads():
    pattern = r'^## (\d\d) · ([^\n]+?) · \d+:\d+–\d+:\d+\n\n\*\*Narration\*\*\n\n(.*?)\n\n\*\*Picture:\*\*'
    result = re.findall(pattern, SCRIPT.read_text(), re.S | re.M)
    assert [n for n, _, _ in result] == [f'{i:02}' for i in range(1, 9)]
    assert sum(len(text.split()) for _, _, text in result) == 1217
    return result


def voice_align(reads, lock, takes, independent, workers):
    path = takes / 'alignment-v2.json'
    cached = json.loads(path.read_text()) if path.exists() else {}
    results, jobs = {}, []
    for n, _, text in reads:
        info = lock['takes'][n]
        wave_path = takes / info['file']
        assert digest(wave_path) == info['sha256']
        hit = cached.get(n, {})
        if hit.get('sha256') == info['sha256'] and hit.get('text') == text and (not independent or hit.get('diagnostic')):
            results[n] = hit
        else:
            jobs.append((n, wave_path, text, independent))
    if jobs:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for n, result in pool.map(align_job, jobs):
                results[n] = result
                print(f'Aligned take {n}: {len(result["spans"])} tokens; {result["duration"]:.3f}s', flush=True)
        path.write_text(json.dumps(results, indent=2) + '\n')
    return results


def trim_native(path, spans):
    y = read_native(path)
    active = np.flatnonzero(np.abs(y) > 10 ** (-55 / 20))
    assert np.abs(y).max() < .96 and len(active) > SOURCE_RATE
    assert abs(active[0] / SOURCE_RATE - spans[0]['start']) < .16
    assert abs(active[-1] / SOURCE_RATE - spans[-1]['end']) < .20
    head = max(0, min(active[0], math.floor(spans[0]['start'] * SOURCE_RATE)) - round(.045 * SOURCE_RATE))
    tail = min(len(y), max(active[-1] + 1, math.ceil(spans[-1]['end'] * SOURCE_RATE)) + round(.12 * SOURCE_RATE))
    stem = y[head:tail].copy()
    n = round(.008 * SOURCE_RATE)
    assert max(np.abs(stem[:n]).max(), np.abs(stem[-n:]).max()) < 10 ** (-47 / 20)
    fade = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    stem[:n] *= fade
    stem[-n:] *= fade[::-1]
    return resample_poly(stem, 160, 147), int(head), int(len(y) - tail)


def write24(f, y):
    quantized = np.rint(y * ((1 << 23) * 10 ** (GAIN_DB / 20))).astype('<i4')
    assert np.max(np.abs(quantized)) < (1 << 23)
    f.writeframesraw(quantized.view('uint8').reshape(-1, 4)[:, :3].tobytes())


def plain(s):
    return s.strip('.,:;?!').lower()


def protected_breaks(display):
    plain_words = [plain(w) for w in display]
    blocked = set()
    for phrase in KEEP_TOGETHER:
        phrase_words = phrase.lower().split()
        for i in range(len(display) - len(phrase_words) + 1):
            if plain_words[i:i + len(phrase_words)] == phrase_words:
                blocked.update(range(i + 1, i + len(phrase_words)))
    return blocked


def break_penalty(previous, after):
    if previous[-1] in '.?!':
        return 0
    if previous[-1] in ',:;':
        return .24
    if plain(previous) in WEAK_END:
        return 3.8
    if plain(after) in {'and', 'but', 'or', 'because', 'while', 'when'}:
        return .44
    return .92


def wrap(display, i, j, blocked):
    straight = ' '.join(display[i:j])
    if len(straight) <= 42:
        return [straight], 0.0
    if len(straight) > 85:
        return None
    best = None
    for split in range(i + 1, j):
        if split in blocked:
            continue
        left, right = ' '.join(display[i:split]), ' '.join(display[split:j])
        if max(len(left), len(right)) > 42:
            continue
        cost = abs(len(left) - len(right)) * .012 + break_penalty(display[split - 1], display[split]) * .30
        key = (cost, [left, right])
        if best is None or key < best:
            best = key
    return (best[1], best[0]) if best is not None else None


def partition(text, spans, stop_before):
    """Choose readable breaks over canonically spelled display words.

    Display tokens (e.g. 2024 and sixty-nine) may cover more than one spoken
    token. Each displayed line is <= 42 chars; display text is never rewritten.
    """
    display, starts, releases = text.split(), [], []
    blocked = protected_breaks(display)
    pos = 0
    cues = []
    mandatory = set()
    for phrase in CAPTION_STARTS:
        option = phrase.split()
        mandatory.update(i for i in range(1, len(display)) if display[i:i + len(option)] == option)
    paragraph_tokens = 0
    for paragraph in text.split('\n\n')[:-1]:
        paragraph_tokens += len(paragraph.split())
        mandatory.add(paragraph_tokens)
    n = len(display)
    for w in display:
        parts = tokens(w)
        assert parts and [t['word'] for t in spans[pos:pos + len(parts)]] == parts
        first = spans[pos]['start']
        starts.append(round(min(first, max(first - .055, spans[pos - 1]['end'] if pos else 0.0)) * 1000))
        pos += len(parts)
        releases.append(spans[pos - 1]['end'])
    starts.append(round(stop_before * 1000))
    assert pos == len(spans)
    assert all(a < b for a, b in zip(starts, starts[1:]))
    scores = [float('inf')] * n + [0.0]
    best = {}
    for i in reversed(range(n)):
        if i in blocked:
            continue
        for j in range(i + 1, min(i + 20, n) + 1):
            if (j - 1 > i and j - 1 in mandatory) or starts[j] - starts[i] > 7200:
                break
            if j in blocked or scores[j] == float('inf'):
                continue
            layout = wrap(display, i, j, blocked)
            if not layout:
                continue
            lines, wrap_cost = layout
            nchar = len(' '.join(lines))
            hold = .36 if display[j - 1].endswith(('.', '?', '!')) else .30
            e = min(starts[j], round((releases[j - 1] + hold) * 1000))
            duration = (e - starts[i]) / 1000
            if not 1.00 <= duration <= 6.55 or nchar / duration > CPS:
                continue
            # Prefer sentence endings, sensible lines and good reading time.
            inner_stops = sum(w.endswith(('.', '?', '!')) for w in display[i:j-1])
            score = (scores[j] + .5 + .075 * (duration - 3.25) ** 2 + .34 * inner_stops + wrap_cost
                     + (break_penalty(display[j-1], display[j]) if j < n and j not in mandatory else 0))
            if score < scores[i]:
                scores[i], best[i] = score, (j, lines, e, nchar / duration)
    i = 0
    while i < n:
        assert i in best, ('Caption layout failed', display[max(i - 4, 0):i + 10])
        j, lines, e, cps = best[i]
        cues.append({'lines': lines, 'in_ms': starts[i], 'out_ms': e, 'cps': cps})
        i = j
    assert ' '.join(line for cue in cues for line in cue['lines']) == ' '.join(display)
    return cues


def phrase_onset(spans, phrase):
    ref = tokens(phrase)
    seq = [s['word'] for s in spans]
    hits = [i for i in range(len(seq)) if seq[i:i + len(ref)] == ref]
    assert len(hits) == 1, (phrase, hits)
    return spans[hits[0]]['start']


def timing(qa, beats):
    rows = [
        '# Extinct Life — Atlantic Tracks: timed VO v2', '',
        '**Why These Dinosaur Footprints Are an Ocean Apart**', '',
        f'**{tc(qa["duration_seconds"])}** measured dry narration, same selected English narrator as v1. '
        'Use only the v2 WAV and v2 subtitles together. No pitch change or time stretch.', '',
        f'- `{STEM}.wav`: 48 kHz / 24-bit mono PCM. No music or Foley.',
        f'- `{STEM}.en.srt`: {qa["cue_count"]} English cues starting at the WAV’s timeline zero.',
        f'- Dry track: {qa["audio"]["integrated_lufs"]:.2f} LUFS-I, {qa["audio"]["true_peak_dbtp"]:.2f} dBTP; not the final programme mix.',
        '- Script v2 · '
        'Opening board · '
        'Evidence and rights', '',
        '## Scene windows', '',
        'Cut windows use the gaps between sections, not the estimated script headings or release chapters.', '',
        '| Section | Edit window | Speech in |', '|---|---|---|',
    ]
    for c in qa['scenes']:
        rows.append(f'| {c["section"]}. {c["title"]} | {tc(c["edit_in"])}–{tc(c["edit_out"])} | {tc(c["speech_start"])} |')
    rows += ['', '## On the spoken line', '',
             'Word-aligned onset estimates; fine-trim to the audio in the edit. Rough cuts may use the scene windows above.', '',
             '| Time | Phrase | Picture cue |', '|---|---|---|']
    rows += [f'| {tc(b["seconds"])} | {b["phrase"]} | {b["picture"]} |' for b in beats]
    rows += ['', 'No press or journal art is needed for this cut. The 125 Ma panel is model geography, not a track date. '
             'Use a possible land route, never a measured or witnessed dinosaur journey. Confirm proper-name playback before picture lock. '
             'End credits can extend the film beyond the measured dry VO.', '']
    return '\n'.join(rows)


def build(arg, reads, lock, alignment):
    arg.out.mkdir(parents=True, exist_ok=True)
    master = arg.out / f'{STEM}.wav'
    first_sample = round(.08 * OUT_RATE)
    cursor, scenes, shifted = first_sample, [], {}
    with wave.open(str(master), 'wb') as f:
        f.setparams((1, 3, OUT_RATE, 0, 'NONE', 'not compressed'))
        f.writeframesraw(bytes(first_sample * 3))
        for idx, (n, title, text) in enumerate(reads):
            aligned = alignment[n]['spans']
            clip, head, tail = trim_native(arg.takes / lock['takes'][n]['file'], aligned)
            offset = cursor / OUT_RATE - head / SOURCE_RATE
            shifted[n] = [{**w, 'start': w['start'] + offset, 'end': w['end'] + offset} for w in aligned]
            write24(f, clip)
            scenes.append(dict(section=int(n), title=title, start_sample=cursor, end_sample=cursor+len(clip),
                               speech_start=shifted[n][0]['start'], speech_end=shifted[n][-1]['end'],
                               trimmed_head_source_frames=head, trimmed_tail_source_frames=tail))
            pad = round((HOLD[idx] if idx < len(HOLD) else .55) * OUT_RATE)
            f.writeframesraw(bytes(pad * 3))
            cursor += len(clip) + pad
    duration = cursor / OUT_RATE
    assert 420 <= duration < 480, duration
    assert .06 < scenes[0]['speech_start'] < .18
    assert all(.38 < b['speech_start'] - a['speech_end'] < .90 for a, b in zip(scenes, scenes[1:]))
    with wave.open(str(master), 'rb') as f:
        assert (f.getframerate(), f.getsampwidth(), f.getnchannels(), f.getnframes()) == (OUT_RATE, 3, 1, cursor)
    edit_start = 0.0
    cues = []
    for idx, (n, _, text) in enumerate(reads):
        scene = scenes[idx]
        next_speech = scenes[idx + 1]['speech_start'] if idx + 1 < len(scenes) else duration
        edit_end = (scene['speech_end'] + next_speech) / 2 if idx + 1 < len(scenes) else duration
        scene.update(edit_in=edit_start, edit_out=edit_end)
        edit_start = edit_end
        cues.extend(partition(text, shifted[n], next_speech - .055))
    assert all(a['out_ms'] <= b['in_ms'] for a, b in zip(cues, cues[1:]))
    assert cues[-1]['out_ms'] < duration * 1000
    subs = arg.out / f'{STEM}.en.srt'
    blocks = [f'{i}\n{timestamp(c["in_ms"])} --> {timestamp(c["out_ms"])}\n' + '\n'.join(c['lines'])
              for i, c in enumerate(cues, 1)]
    subs.write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    volume = loudness(['-i', str(master)])
    assert -22 < volume['integrated_lufs'] < -18 and volume['true_peak_dbtp'] <= -2.5, volume
    quiet = ffmpeg(['-i', str(master), '-af', 'silencedetect=noise=-50dB:d=0.85', '-f', 'null', '-'])
    pauses = [float(x) for x in re.findall(r'silence_duration: (\d+(?:\.\d+)?)', quiet)]
    assert not pauses or max(pauses) < 1.15, pauses
    beats = [{'seconds': phrase_onset(shifted[f'{n:02}'], phrase), 'phrase': phrase, 'picture': pic} for n, phrase, pic in BEATS]
    assert all(a['seconds'] < b['seconds'] for a, b in zip(beats, beats[1:]))
    qa = {'script_sha256': lock['script_sha256'],
          'repository_script_sha256': lock.get('repository_script_sha256', lock['script_sha256']),
          'voice_selection': lock['voice_selection'],
          'source_words': 1217, 'duration_seconds': duration, 'sample_frames': cursor,
          'sample_rate': OUT_RATE, 'bit_depth': 24, 'channels': 1,
          'audio': {**volume, 'static_gain_db': GAIN_DB}, 'cue_count': len(cues),
          'maximum_caption_chars_per_second': round(max(c['cps'] for c in cues), 2),
          'quiet_intervals_at_least_0_85_seconds': pauses, 'no_pitch_shift_or_time_stretch': True,
          'scenes': scenes, 'opening_rewind_estimate_s': beats[3]['seconds'],
          'alignment': '10 ms word alignment, not human playback certification'}
    sheet = arg.out / f'{STEM}-Timing.md'
    sheet.write_text(timing(qa, beats), encoding='utf-8')
    qa['files'] = [{'file': x.name, 'size': x.stat().st_size, 'sha256': digest(x)} for x in (master, subs, sheet)]
    arg.receipt.write_text(json.dumps(qa, indent=2) + '\n')
    print(f'{tc(duration)} · {qa["source_words"]} script words · {len(cues)} SRT cues · {qa["maximum_caption_chars_per_second"]:.2f} peak cps')
    print(volume, 'quiet spans ≥0.85s', pauses)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--takes', type=Path, default=TAKES)
    p.add_argument('--out', type=Path, default=OUT)
    p.add_argument('--receipt', type=Path, default=HERE / 'vo-v2-receipt.json')
    p.add_argument('--probe', action='store_true', help='run independent decode and forced alignment, no exports')
    p.add_argument('--workers', type=int, default=4)
    a = p.parse_args()
    lock = json.loads(LOCK.read_text())
    assert digest(SCRIPT) in (lock['script_sha256'], lock.get('repository_script_sha256'))
    text = reads()
    alignment = voice_align(text, lock, a.takes, a.probe, a.workers)
    if not a.probe:
        build(a, text, lock, alignment)


if __name__ == '__main__':
    main()
