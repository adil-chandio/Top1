"""
Monarch V6 Hollywood IMAX Cinema SDK — Streaming Decoded-MP4 Forensic Validator (`forensic_qa_sdk.py`).
Uses O(1)-memory (`< 6 MB` RAM) frame-by-frame FFmpeg streaming so both 35-second Shorts and
full 5-to-60-minute IMAX Documentaries validate cleanly inside 4 GB containers!
Verifies:
  1. Exact decoded frame count == `expected_frames`, 0 decode errors, 0 black frames (`min_luma > 8.0`)
  2. Zero `A -> B -> A` single-frame flicker spikes across all non-cut triplets
  3. Seamless loop ROI MAE `< max_loop_mae` (when `check_seamless_loop=True`)
  4. Muxed EBU R128 Integrated Loudness (`-15.4 .. -13.2 LUFS`) & True Peak (`<= -0.9 dBFS`)
  5. Optional Pre-Twist Vacuum Silence RMS (`< -48.0 dBFS`)
"""
import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
import numpy as np


def find_ffmpeg() -> str:
    matches = glob.glob("/tmp/py/imageio_ffmpeg/binaries/ffmpeg*")
    return matches[0] if matches else "ffmpeg"


def verify_imax_mp4(
    mp4_path: str,
    expected_frames: int,
    shot_cuts: set,
    check_seamless_loop: bool = True,
    max_loop_mae: float = 9.5,
    vacuum_window_s: tuple = None,
    line_windows: list = None,
    max_line_spread_db: float = 4.2,
    max_hiss_floor_db: float = None,
    scale_w: int = 320,
    scale_h: int = 180,
) -> dict:
    assert os.path.isfile(mp4_path), f"Missing MP4: {mp4_path}"
    ffmpeg = find_ffmpeg()
    frame_bytes = scale_w * scale_h * 3

    # 1 & 2. O(1)-memory streaming raw RGB decode + luma + A->B->A single-frame flicker audit!
    proc = subprocess.Popen(
        [
            ffmpeg, "-v", "error", "-i", mp4_path,
            "-vf", f"scale={scale_w}:{scale_h}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    n_frames = 0
    min_luma = 999.0
    first_frame = None
    f_prev2 = None
    f_prev1 = None
    aba_spikes = []

    while True:
        buf = proc.stdout.read(frame_bytes)
        if not buf:
            break
        assert len(buf) == frame_bytes, f"Truncated frame bytes at idx={n_frames}: {len(buf)}"
        cur = np.frombuffer(buf, dtype=np.uint8).reshape((scale_h, scale_w, 3)).astype(np.float32)
        luma = float(cur.mean())
        if luma < min_luma:
            min_luma = luma
        if n_frames == 0:
            first_frame = cur.copy()

        # Check triplet (f_prev2, f_prev1, cur) centered at idx = n_frames - 1
        mid_idx = n_frames - 1
        if f_prev2 is not None and not any(abs(mid_idx - c) <= 2 for c in shot_cuts):
            d_prev = float(np.abs(f_prev1 - f_prev2).mean())
            d_next = float(np.abs(cur - f_prev1).mean())
            d_bridge = float(np.abs(cur - f_prev2).mean())
            if d_prev > 14.0 and d_next > 14.0 and d_bridge < 4.5:
                aba_spikes.append((mid_idx, round(d_prev, 2), round(d_next, 2), round(d_bridge, 2)))

        f_prev2 = f_prev1
        f_prev1 = cur
        n_frames += 1

    stderr_out = proc.stderr.read().decode("utf-8", errors="replace")
    ret = proc.wait()
    assert ret == 0 and stderr_out == "", f"FFmpeg decode errors (ret={ret}): {stderr_out}"
    assert n_frames == expected_frames, f"Expected {expected_frames} decoded frames, got {n_frames}"
    assert min_luma > 8.0, f"Black/dropped frame detected! min_luma={min_luma:.2f}"
    assert len(aba_spikes) == 0, f"Detected A->B->A flicker spikes: {aba_spikes[:10]}"

    # 3. Seamless loop check
    loop_mae = None
    if check_seamless_loop and first_frame is not None and f_prev1 is not None:
        roi_last = f_prev1[int(scale_h * 0.14):int(scale_h * 0.62), :, :]
        roi_first = first_frame[int(scale_h * 0.14):int(scale_h * 0.62), :, :]
        loop_mae = float(np.abs(roi_last - roi_first).mean())
        assert loop_mae < max_loop_mae, f"Loop seam MAE too high: {loop_mae:.3f} >= {max_loop_mae}"

    # 4. Muxed EBU R128 loudness check
    res = subprocess.run(
        [ffmpeg, "-nostats", "-i", mp4_path, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    m_i = re.findall(r"I:\s*(-?\d+\.\d+)\s*LUFS", res.stderr)
    m_tp = re.findall(r"Peak:\s*(-?\d+\.\d+)\s*dBFS", res.stderr)
    assert m_i and m_tp, "Failed to parse EBU R128 summary"
    lufs = float(m_i[-1])
    tp = float(m_tp[-1])
    assert -15.4 <= lufs <= -13.2, f"Loudness out of broadcast range: {lufs} LUFS"
    assert tp <= -0.9, f"True peak too hot: {tp} dBFS"

    # 5. Optional pre-twist vacuum silence check
    vac_rms_db = None
    if vacuum_window_s is not None:
        t0, t1 = vacuum_window_s
        pcm = subprocess.run(
            [
                ffmpeg, "-v", "error",
                "-ss", f"{t0:.4f}", "-to", f"{t1:.4f}",
                "-i", mp4_path,
                "-vn", "-f", "f32le", "-ac", "2", "-ar", "48000", "-",
            ],
            capture_output=True, check=True,
        ).stdout
        audio = np.frombuffer(pcm, dtype=np.float32).reshape((-1, 2))
        vac_rms_db = float(20.0 * np.log10(np.sqrt(np.mean(audio ** 2)) + 1e-9))
        assert vac_rms_db < -48.0, f"Pre-twist vacuum drop too noisy: {vac_rms_db:.1f} dBFS"

    # 6. Optional V7 Per-Line Dialogue Consistency & Stationary Hiss/Buzz Floor Audit on Decoded AAC!
    line_spread_db = None
    hiss_floor_db = None
    if line_windows is not None or max_hiss_floor_db is not None:
        from scipy import signal as _sig
        full_pcm = subprocess.run(
            [ffmpeg, "-v", "error", "-i", mp4_path, "-vn", "-f", "f32le", "-ac", "2", "-ar", "48000", "-"],
            capture_output=True, check=True,
        ).stdout
        full_aud = np.frombuffer(full_pcm, dtype=np.float32).reshape((-1, 2))
        mono_aud = np.mean(full_aud, axis=1)

        if line_windows:
            line_dbs = []
            win = int(0.018 * 48000)
            kern = np.ones(win, dtype=np.float32) / win
            for ln in line_windows:
                s0, s1 = int(ln["t0"] * 48000), int(ln["t1"] * 48000)
                seg = mono_aud[s0:s1]
                env = np.sqrt(np.convolve(seg ** 2, kern, mode="same"))
                p95 = float(np.percentile(env, 95))
                voiced = env >= max(0.002, p95 * 0.25)
                rms = float(np.sqrt(np.mean(seg[voiced] ** 2)) + 1e-12)
                line_dbs.append(20.0 * np.log10(rms))
            line_spread_db = float(max(line_dbs) - min(line_dbs))
            assert line_spread_db <= max_line_spread_db, (
                f"Post-AAC dialogue level inconsistent! spread={line_spread_db:.2f} dB > {max_line_spread_db} dB"
            )

        if max_hiss_floor_db is not None:
            sos_h = _sig.butter(4, [2500.0 / 24000.0, 7000.0 / 24000.0], btype="bandpass", output="sos")
            hi = _sig.sosfilt(sos_h, mono_aud)
            wlen = int(0.10 * 48000)
            nw = len(hi) // wlen
            wrms = np.sqrt(np.mean(hi[: nw * wlen].reshape(nw, wlen) ** 2, axis=1))
            hiss_floor_db = float(20.0 * np.log10(float(np.percentile(wrms, 15)) + 1e-12))
            assert hiss_floor_db <= max_hiss_floor_db, (
                f"Post-AAC stationary hiss/buzz floor too high: {hiss_floor_db:.1f} dBFS > {max_hiss_floor_db} dBFS"
            )

    return {
        "decoded_frames": n_frames,
        "min_luma": min_luma,
        "aba_spikes": 0,
        "loop_mae": loop_mae,
        "lufs": lufs,
        "true_peak_dbfs": tp,
        "vacuum_rms_db": vac_rms_db,
        "line_spread_db": line_spread_db,
        "hiss_floor_db": hiss_floor_db,
    }
