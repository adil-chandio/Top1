"""Reference AV inspection via GitHub-hosted public media + local decoding.

Verified in this workspace (2026-11-16):
- youtube.com / instagram.com / tiktok.com: BLOCKED (network 000)
- api.github.com: 200 OK
- pypi.org: 200 OK
- raw.githubusercontent.com: BLOCKED

Therefore reference media is fetched from GitHub-hosted public files through
the API (Accept: application/vnd.github.raw+json), then decoded locally with
FFmpeg. This produces genuine `video_viewed` evidence (real frames inspected)
and genuine `audio_analysed` evidence (real spectral + onset analysis).

Honest limits, stated in every evidence record:
- competitor platform playback is NOT established;
- ASR transcription is NOT available (model host blocked); audio analysis is
  spectral/onset-based, not speech recognition;
- audio_listened is reported as `spectral_analysed`, never as `audio_listened`
  unless an actual listening-capable executor recorded it.
"""
import hashlib,json,os,subprocess,sys,wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _numpy():
    for extra in ('/tmp/pydeps',):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    import numpy as np
    return np


def ffmpeg():
    env = os.getenv('ACCOUNTS_FFMPEG') or os.getenv('FFMPEG')
    if env and Path(env).is_file():
        return env
    try:
        import imageio_ffmpeg
        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(candidate).is_file():
            return candidate
    except Exception:
        pass
    for extra in ('/tmp/pydeps',):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    try:
        import imageio_ffmpeg
        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(candidate).is_file():
            return candidate
    except Exception:
        return None


def download(repo, path, dest, ref=None):
    """Fetch a public media file through the GitHub API and hash it."""
    import urllib.parse, urllib.request
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size:
        return {'path': str(dest), 'bytes': dest.stat().st_size,
                'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                'cached': True}
    dest.parent.mkdir(parents=True, exist_ok=True)
    query = f'?ref={urllib.parse.quote(ref)}' if ref else ''
    url = f'https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(path)}{query}'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github.raw+json',
        'User-Agent': 'accounts-studio-reference',
    })
    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read()
    if not data:
        raise RuntimeError('empty response for reference media')
    dest.write_bytes(data)
    return {'path': str(dest), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(), 'cached': False}


def probe(media):
    exe = ffmpeg()
    if not exe:
        raise RuntimeError('FFmpeg required for reference inspection')
    out = subprocess.run([exe, '-hide_banner', '-i', str(media)],
                         capture_output=True, text=True)
    info = {'raw': out.stderr[-4000:]}
    for line in out.stderr.splitlines():
        line = line.strip()
        if line.startswith('Duration:'):
            info['duration'] = line.split('Duration:')[1].split(',')[0].strip()
        elif line.startswith('Stream #0:0') or line.startswith('Stream #0:1'):
            info.setdefault('streams', []).append(line)
    return info


def frames(media, out_dir, times, width=480):
    exe = ffmpeg()
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    produced = []
    for t in times:
        dest = out_dir / f'f_{str(t).replace(".", "_")}.jpg'
        proc = subprocess.run(
            [exe, '-y', '-hide_banner', '-loglevel', 'error',
             '-ss', str(t), '-i', str(media), '-map', '0:v:0',
             '-frames:v', '1', '-vf', f'scale={width}:-2', str(dest)],
            capture_output=True, text=True)
        if dest.is_file() and dest.stat().st_size:
            produced.append({'time': t, 'path': str(dest),
                             'bytes': dest.stat().st_size,
                             'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    if not produced:
        raise RuntimeError('no frames extracted: ' + (proc.stderr[-500:] if proc else ''))
    return produced


def audio_wav(media, dest, rate=16000, channel=1):
    exe = ffmpeg()
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, '-y', '-hide_banner', '-loglevel', 'error',
                    '-i', str(media), '-map', '0:a:0',
                    '-ac', str(channel), '-ar', str(rate), str(dest)],
                   check=True, capture_output=True)
    return dest


def spectral(wav_path, sample_seconds=(0, 4, 9, 12, 15, 20, 30, 40, 50)):
    """Real spectral + onset analysis. Not speech recognition."""
    np = _numpy()
    with wave.open(str(wav_path), 'rb') as handle:
        rate = handle.getframerate()
        data = np.frombuffer(handle.readframes(handle.getnframes()),
                             dtype=np.int16).astype(np.float32) / 32768.0
    n, hop = 2048, 512
    rows = []
    for i in range(0, len(data) - n, hop):
        window = data[i:i + n] * np.hanning(n)
        spec = np.abs(np.fft.rfft(window))
        freqs = np.fft.rfftfreq(n, 1 / rate)
        total = spec.sum() + 1e-9
        rows.append((
            i / rate,
            float((spec * freqs).sum() / total),
            float(spec[(freqs >= 20) & (freqs < 250)].sum() / total),
            float(spec[(freqs >= 250) & (freqs < 2000)].sum() / total),
            float(spec[(freqs >= 300) & (freqs < 3400)].sum() / total),
            float(spec[(freqs >= 2000) & (freqs < 8000)].sum() / total),
            float(np.sqrt((data[i:i + n] ** 2).mean())),
        ))
    arr = np.array(rows)
    timeline = []
    for second in sample_seconds:
        index = int(second * rate / hop)
        if index >= len(arr):
            continue
        _, centroid, low, mid, speech, high, rms = arr[index]
        timeline.append({
            't': second, 'centroid_hz': round(centroid),
            'low_pct': round(low * 100), 'mid_pct': round(mid * 100),
            'speech_band_pct': round(speech * 100), 'high_pct': round(high * 100),
            'rms': round(float(rms), 4),
            'label': ('silence' if rms < 0.01 else
                      'active_low' if centroid < 1500 else
                      'active_mid' if centroid < 2500 else 'active_high'),
        })
    energy = arr[:, 6]
    deltas = np.diff(energy)
    onset_idx = np.where(deltas > np.percentile(deltas, 97))[0]
    onset_times = [round(float(arr[i, 0]), 2) for i in onset_idx]
    return {
        'duration_s': round(len(data) / rate, 2),
        'sample_rate': rate,
        'peak': round(float(np.abs(data).max()), 4),
        'rms': round(float(np.sqrt((data ** 2).mean())), 4),
        'mean_centroid_hz': round(float(arr[:, 1].mean())),
        'silence_ratio': round(float((energy < 0.01).mean()), 3),
        'loudest_at_s': round(float(arr[energy.argmax(), 0]), 2),
        'onset_count': len(onset_times),
        'onsets_s': onset_times[:40],
        'timeline': timeline,
        'method': 'fft_spectral_plus_onset_energy',
        'access_label': 'spectral_analysed',
        'not_claimed': ['speech_recognition', 'audio_listened_by_human_executor'],
    }
