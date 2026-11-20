#!/usr/bin/env python3
"""Assemble the approved English takes without altering their pace or pitch.

Python 3.11+, NumPy 2.2.6, SciPy 1.15.3, PocketSphinx 5.0.4,
imageio-ffmpeg 0.6.0. The tool snapshots only the specified take files;
regeneration by a TTS service is not deterministic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import wave

import imageio_ffmpeg
import numpy as np
from pocketsphinx import Decoder
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE.parent / 'step-2/Extinct-Life-Atlantic-Tracks-Script-v1.md'
TAKES = ROOT / '.cache/monarch-extinct/atlantic-tracks/voice-v1'
OUT = ROOT / 'deliverables/extinct-life-step-3'
STEM = 'Extinct-Life-Atlantic-Tracks-VO-v1'
OUT_RATE = 48_000
SOURCE_RATE = 44_100
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")
NORMAL = r'\(\d+\)$'
HOLD = (.46, .50, .47, .52, .48, .52)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# Approximate marker onsets follow the spoken phrase; none is a release chapter.
BEATS = (
    (1, 'Three-toed dinosaur', 'Open on the labelled track schematic and the present-day map.'),
    (1, 'More in Cameroon', 'Light the second locality marker.'),
    (1, 'six thousand kilometres', 'Show ≈6,000 km TODAY. No travel arrow.'),
    (1, 'But the ocean came later', 'Match-cut to the 125 Ma model. Label it RECONSTRUCTION, not a track date.'),
    (2, 'a thousand kilometres apart', 'Show ≈1,000 km THEN as the study estimate, not the distance of a walk.'),
    (3, 'Even the same foot', 'One generic stamp, two substrates. Label the comparison as an illustration.'),
    (4, 'four distinct surfaces', 'Reveal four track-bearing surfaces as separate layers, not one herd.'),
    (4, 'sixty-nine centimetres', 'Ruler for one ~69 cm impression; no claim about the animal’s height.'),
    (4, 'Ripples show', 'Ripple pattern → mud cracks. Use original diagrams.'),
    (4, 'thin mats of microbes', 'Thin schematic layer; do not imply a photographed micrograph.'),
    (5, "In Brazil's Sousa Basin", 'Switch to the Brazilian deposits and rock comparison.'),
    (5, 'including pollen', 'Place the age clue in the surrounding deposits, not in the footprint.'),
    (6, 'Put those clues', 'Return to the old map. Keep both regional markers visible.'),
    (6, "But this isn't a trail", 'Keep the connection as a possible area, not a traced route.'),
    (7, 'the Atlantic widened', 'Return to the modern gap and hold for source credits.'),
)


def digest(p: Path) -> str:
    with p.open('rb') as src:
        return hashlib.file_digest(src, 'sha256').hexdigest()


def words(s: str) -> list[str]:
    return WORD.findall(s.lower())


def ffmpeg(args: list[str], pcm: bytes | None = None) -> str:
    p = subprocess.run([FFMPEG, '-hide_banner', '-nostdin', *args], input=pcm,
                       capture_output=True, timeout=60, check=True)
    return p.stderr.decode()


def loudness(input_args, pcm=None):
    log = ffmpeg([*input_args, '-af', 'loudnorm=I=-18:TP=-2:LRA=12:print_format=json', '-f', 'null', '-'], pcm)
    data = json.loads(re.search(r'\{\s*"input_i".*?\}', log, flags=re.S)[0])
    return {key: float(data[value]) for key, value in (
        ('integrated_lufs', 'input_i'), ('true_peak_dbtp', 'input_tp'), ('range_lu', 'input_lra'))}


def align(audio, transcript):
    d = Decoder(samprate=16_000, frate=100, loglevel='ERROR')
    for name, phones in {
        "cameroon's": 'K AE M ER UW N Z', 'koum': 'K UW M',
        'sousa(2)': 'S OW Z AH', 'gondwana(2)': 'G AA N D W AA N AH',
        'theropod': 'TH EH R AH P AA D',
    }.items():
        if d.lookup_word(name) is None:
            d.add_word(name, phones, False)
    ref = words(transcript)
    assert all(d.lookup_word(w) is not None for w in ref)
    # Align canonical caption spellings, even where the speech input used a
    # phonetic alias for a proper noun. These are modeled word boundaries.
    d.set_align_text(' '.join(ref))
    mono16 = resample_poly(audio, 160, 441)
    buf = np.rint(np.clip(mono16, -1.0, 32767 / 32768) * 32768).astype('<i2').tobytes()
    d.start_utt()
    d.process_raw(buf, full_utt=True)
    d.end_utt()
    aligned = [
        {'word': re.sub(NORMAL, '', t.word), 'start': t.start_frame / 100, 'end': (t.end_frame + 1) / 100}
        for t in d.seg() if not t.word.startswith(('<', '['))
    ]
    assert [v['word'] for v in aligned] == ref
    assert aligned[0]['start'] >= 0 and aligned[-1]['end'] < len(audio) / SOURCE_RATE
    return aligned


def prepare_take(path, take, narration):
    assert digest(path) == take['sha256'], f'Unexpected take bytes: {path}'
    with wave.open(str(path), 'rb') as w:
        assert (w.getframerate(), w.getnchannels(), w.getsampwidth()) == (SOURCE_RATE, 1, 2)
        native = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype('float64') / 32768
    spans = align(native, narration)
    active = np.flatnonzero(np.abs(native) > 10 ** (-55 / 20))
    assert np.abs(native).max() < .96 and len(active) > SOURCE_RATE
    # Keep all audio on the inside of each take. Only remove excess edge pad.
    lead = max(0, min(active[0], math.floor(spans[0]['start'] * SOURCE_RATE)) - round(.046 * SOURCE_RATE))
    tail = min(len(native), max(active[-1] + 1, math.ceil(spans[-1]['end'] * SOURCE_RATE)) + round(.11 * SOURCE_RATE))
    part = native[lead:tail].copy()
    n = round(.008 * SOURCE_RATE)
    assert max(np.abs(part[:n]).max(), np.abs(part[-n:]).max()) < 10 ** (-47 / 20)
    fade = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    part[:n] *= fade
    part[-n:] *= fade[::-1]
    clip = resample_poly(part, up=160, down=147)
    return clip, spans, {'native_frames': len(native), 'trim_head_frames': int(lead), 'trim_tail_frames': int(len(native) - tail)}


def timestamp(ms, sep=','):
    hr, rem = divmod(ms, 3_600_000)
    minute, rem = divmod(rem, 60_000)
    sec, milli = divmod(rem, 1_000)
    return f'{hr:02d}:{minute:02d}:{sec:02d}{sep}{milli:03d}'


def tc(seconds):
    return timestamp(round(seconds * 1000), '.')[3:]


def cue_blocks(path):
    result = []
    for block in path.read_text().strip().split('\n\n'):
        header, *lines = block.splitlines()
        assert header == f'# {len(result)+1:02}'
        groups = [line.split('|') for line in lines]
        assert all(1 <= len(group) <= 2 and all(0 < len(ln) <= 42 for ln in group) for group in groups)
        result.append(groups)
    return result


def captions(cues, duration):
    starts, last = [], 0.0
    for cue in cues:
        starts.append(min(cue['onset'], max(cue['onset'] - .055, last)))
        last = cue['release']
    srt = []
    for i, cue in enumerate(cues):
        begin = round(starts[i] * 1000)
        ends_at = starts[i + 1] if i + 1 < len(cues) else duration
        hold = .24 if cue['lines'][-1][-1] in '.?!' else .15
        end = round(min(ends_at, cue['release'] + hold) * 1000)
        assert 940 <= end - begin <= 6500, (cue, begin, end)
        assert end <= round(ends_at * 1000)
        cue['in_ms'], cue['out_ms'] = begin, end
        cue['chars_per_second'] = len(' '.join(cue['lines'])) / ((end - begin) / 1000)
        srt.append(f'{i+1}\n{timestamp(begin)} --> {timestamp(end)}\n' + '\n'.join(cue['lines']))
    return '\n\n'.join(srt) + '\n'


def phrase_onset(spans, phrase):
    tokens = words(phrase)
    seq = [w['word'] for w in spans]
    matches = [i for i in range(len(seq)) if seq[i:i + len(tokens)] == tokens]
    assert len(matches) == 1, (phrase, matches)
    return spans[matches[0]]['start']


def timing_sheet(scenes, spans, qa):
    duration = qa['duration_seconds']
    rows = [
        '# Extinct Life — Atlantic Tracks: VO v1 and edit timing', '',
        '**Why These Dinosaur Footprints Are an Ocean Apart**', '',
        f'**{tc(duration)}** dry English voice-over, from the narrator selected in the audition. '
        'No added music, Foley or time stretch. The original 4:10 was a script pacing guide, not the timing of this recording.', '',
        f'- **Audio:** `{STEM}.wav` — 48 kHz, 24-bit PCM, mono for the edit. '
        'Native speech rate retained; resampled from the audition service’s 44.1 kHz takes.',
        f'- **Captions:** `{STEM}.en.srt` — {qa["cue_count"]} cues, matched to this WAV. WAV and SRT share 00:00 as the start; do not apply a separate offset.',
        '- **Text and picture:** Script v1 · '
        'Evidence · '
        'Opening board.',
        '- **Audio check:** {integrated_lufs:.2f} LUFS-I, {true_peak_dbtp:.2f} dBTP. These are dry track levels, not the final programme mix.'.format(**qa['audio']),
        '', '## Sequence', '',
        'Times below mark edit windows (cuts between spoken sections). The added slates, credits and final cut may change the video runtime.', '',
        '| Section | Edit window | First word |', '|---|---|---|',
    ]
    start = 0.0
    for i, scene in enumerate(scenes):
        end = (scene['speech_end'] + scenes[i + 1]['speech_start']) / 2 if i + 1 < len(scenes) else duration
        rows.append(f'| {i+1}. {scene["title"]} | {tc(start)}–{tc(end)} | {tc(scene["speech_start"])} |')
        start = end
    rows += ['', '## Picture cues', '',
             'Cue onsets are approximate word-alignment times. Match to the sound in the edit rather than treating milliseconds as exact phoneme boundaries.', '',
             '| Time | On the line | Picture |', '|---|---|---|']
    for i, phrase, picture in BEATS:
        rows.append(f'| {tc(phrase_onset(spans[i-1], phrase))} | {phrase} | {picture} |')
    rows += ['', 'Keep the tracks at two separate sites and use the reconstructed land as a **possible** dispersal area. '
             'No matched fossil pair, continuous trail, or reused press photo is needed. Do a playback/pronunciation check before picture lock.', '']
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--takes', type=Path, default=TAKES)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--receipt', type=Path, default=HERE / 'vo-v1-receipt.json')
    arg = parser.parse_args()
    lock = json.loads((HERE / 'take-lock.json').read_text())
    assert digest(SCRIPT) == lock['script_sha256'], 'The approved script bytes have changed'
    pattern = r'^## \d+:\d+–\d+:\d+ · ([^\n]+)\n\n\*\*Narration\*\*\n\n([^\n]+)'
    scenes = re.findall(pattern, SCRIPT.read_text(), flags=re.M)
    groups = cue_blocks(HERE / 'caption-groups.txt')
    assert len(scenes) == len(groups) == len(lock['takes']) == len(HOLD) + 1
    pieces = [np.zeros(round(.080 * OUT_RATE))]
    cursor = len(pieces[0])
    cues, times, chapters = [], [], []
    for i, ((title, narration), block, take) in enumerate(zip(scenes, groups, lock['takes'], strict=True)):
        flattened = ' '.join(' '.join(cue) for cue in block)
        assert flattened == narration, (i + 1, flattened)
        clip, spans, report = prepare_take(arg.takes / take['file'], take, narration)
        off = cursor / OUT_RATE - report['trim_head_frames'] / SOURCE_RATE
        for word in spans:
            for key in ('start', 'end'):
                word[key] += off
        times.append(spans)
        chapters.append(dict(chapter=i+1, title=title, start_sample=cursor, end_sample=cursor+len(clip),
                             speech_start=spans[0]['start'], speech_end=spans[-1]['end'], **report))
        pieces.append(clip)
        pad = np.zeros(round((HOLD[i] if i < len(HOLD) else .48) * OUT_RATE))
        pieces.append(pad)
        cursor += len(clip) + len(pad)
        n = 0
        for lines in block:
            size = len(words(' '.join(lines)))
            cues.append(dict(lines=lines, onset=spans[n]['start'], release=spans[n + size - 1]['end']))
            n += size
        assert n == len(spans)
    master = np.concatenate(pieces)
    duration = len(master) / OUT_RATE
    assert 175 < duration < 205
    assert max(abs(master[0]), abs(master[-1])) == 0.0
    assert all(.36 <= b['speech_start'] - a['speech_end'] < 1.0 for a, b in zip(chapters, chapters[1:]))
    raw = ['-f', 'f64le', '-ar', str(OUT_RATE), '-ac', '1', '-i', 'pipe:0']
    dry = loudness(raw, master.astype('<f8', copy=False).tobytes())
    # Use one linear attenuation for the entire VO, no compression, limiter or EQ.
    gain_db = min(0, -2.65 - dry['true_peak_dbtp'])
    master *= 10 ** (gain_db / 20)
    sample_peak = 20 * math.log10(np.max(np.abs(master)))
    srt = captions(cues, duration)
    arg.out.mkdir(parents=True, exist_ok=True)
    wav = arg.out / f'{STEM}.wav'
    quantized = np.rint(master * (1 << 23)).astype('<i4')
    assert np.abs(quantized).max() < (1 << 23)
    with wave.open(str(wav), 'wb') as f:
        f.setparams((1, 3, OUT_RATE, len(master), 'NONE', 'not compressed'))
        f.writeframes(quantized.view('uint8').reshape(-1, 4)[:, :3].tobytes())
    stats = loudness(['-i', str(wav)])
    with wave.open(str(wav), 'rb') as f:
        assert (f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()) == (OUT_RATE, 1, 3, len(master))
    assert stats['true_peak_dbtp'] <= -2.5 and -22.0 < stats['integrated_lufs'] < -18.0
    first_non_silent = np.flatnonzero(np.abs(master) > 10 ** (-50 / 20))[0] / OUT_RATE
    assert .06 < first_non_silent < .18
    last_lap = max(x['out_ms'] for x in cues) / 1000
    assert last_lap < duration
    max_reading_rate = max(x['chars_per_second'] for x in cues)
    assert max_reading_rate < 26.0, max_reading_rate
    summary = {
        'duration_seconds': duration, 'sample_frames': len(master), 'sample_rate': OUT_RATE, 'bit_depth': 24,
        'channels': 1, 'cue_count': len(cues), 'maximum_caption_chars_per_second': round(max_reading_rate, 2),
        'audio': {**stats, 'sample_peak_dbfs': round(float(sample_peak), 2), 'static_gain_db': round(gain_db, 2)},
        'first_audible_seconds_at_minus_50_dbfs': float(first_non_silent), 'last_caption_end_seconds': last_lap,
        'source_words': sum(len(narration.split()) for _, narration in scenes),
        'no_pitch_shift_or_time_stretch': True, 'timing_basis': 'PocketSphinx alignment at 10 ms + sample-accurate placement',
        'script_sha256': lock['script_sha256'], 'voice_selection': lock['voice_selection'], 'scenes': chapters,
    }
    sub = arg.out / f'{STEM}.en.srt'
    sub.write_text(srt, encoding='utf-8')
    notes = arg.out / f'{STEM}-Timing.md'
    notes.write_text(timing_sheet(chapters, times, summary), encoding='utf-8')
    summary['files'] = [{'file': p.name, 'size': p.stat().st_size, 'sha256': digest(p)} for p in (wav, sub, notes)]
    arg.receipt.write_text(json.dumps(summary, indent=2) + '\n')
    print(f'{tc(duration)} · {summary["source_words"]} words · {len(cues)} SRT cues · {stats["integrated_lufs"]} LUFS-I · {stats["true_peak_dbtp"]} dBTP')
    for x in sorted(cues, key=lambda x: -x['chars_per_second'])[:6]:
        print(f'{x["chars_per_second"]:.1f} cps at {tc(x["in_ms"]/1000)}: ' + ' | '.join(x['lines']))


if __name__ == '__main__':
    main()
