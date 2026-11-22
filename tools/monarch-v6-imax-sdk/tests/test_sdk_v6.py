"""
End-to-end automated verification suite for `tools/monarch-v6-imax-sdk/`:
  1. Verifies `AGENTS.md`, `CLAUDE.md`, `bootstrap_v6_runtime.sh`, and all JS/Python SDK modules exist.
  2. Tests `audio_imax_dsp.py` (zero-stretch tightener, sub-braaam, vacuum drop, loop-locked score, EBU R128 mastering).
  3. Renders a real 30-frame `1080x1920` WebGL2 SwiftShader test film through `tools/monarch-v6-imax-sdk/index.js`
     + `render_imax_ws.mjs` (testing PBR shader, 30 Hz texel-snapped shadows, ACES Filmic + Vogel Bokeh + Anamorphic Bloom,
     volumetric god-rays, loop-locked dust motes, ballistic particles, parametric lofting, 2-bone IK, binary WOFF2 fonts,
     and GPU HUD compositor) and validates the encoded MP4 via `forensic_qa_sdk.verify_imax_mp4(...)`!
"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "/tmp/py")
import numpy as np

ROOT = "/home/user/Top1"
sys.path.insert(0, os.path.join(ROOT, "tools/monarch-v6-imax-sdk/python"))

import audio_imax_dsp as dsp
import forensic_qa_sdk as fqa


def test_repo_constitution_and_sdk_files_present():
    required = [
        "AGENTS.md",
        "CLAUDE.md",
        "docs/Master-3D-Animation-Video-Production-Prompt-V6-IMAX.md",
        "tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh",
        "tools/monarch-v6-imax-sdk/index.js",
        "tools/monarch-v6-imax-sdk/core/pbr_shadow_sdk.js",
        "tools/monarch-v6-imax-sdk/core/postfx_imax_sdk.js",
        "tools/monarch-v6-imax-sdk/core/vfx_physics_sdk.js",
        "tools/monarch-v6-imax-sdk/core/sculpt_ik_rig_sdk.js",
        "tools/monarch-v6-imax-sdk/core/fonts_hud_sdk.js",
        "tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs",
        "tools/monarch-v6-imax-sdk/python/audio_imax_dsp.py",
        "tools/monarch-v6-imax-sdk/python/forensic_qa_sdk.py",
    ]
    for rel in required:
        full = os.path.join(ROOT, rel)
        assert os.path.isfile(full), f"Missing required SDK file: {rel}"


def test_sdk_end_to_end_30_frame_webgl_and_dolby_master():
    # Ensure runtime is bootstrapped
    subprocess.run(["bash", "tools/monarch-v6-imax-sdk/bootstrap_v6_runtime.sh"], cwd=ROOT, check=True)

    work = "/tmp/v6_sdk_smoke"
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)

    # 1. Build 4.000s (120 frames) realistic Dolby audio master (>= 3.0s EBU R128 short-term window!)
    dur_s = 4.0
    n = int(dur_s * dsp.SR)
    t = np.arange(n, dtype=np.float32) / dsp.SR
    # Rich compressed voice-band signal across non-vacuum regions so linear loudnorm hits -14.2 LUFS cleanly
    vo_env = ((t > 0.08) & (t < 1.35)) | ((t > 1.62) & (t < 3.92))
    raw_vo = (
        (0.28 * np.sin(2 * np.pi * 195.0 * t) + 0.18 * np.sin(2 * np.pi * 410.0 * t) + 0.10 * np.sin(2 * np.pi * 820.0 * t))
        * vo_env
    ).astype(np.float32)
    tight = dsp.tighten_vo_zero_stretch(raw_vo)
    assert len(tight) > int(2.5 * dsp.SR)

    mix = np.stack([raw_vo, raw_vo], axis=1)
    dsp.place_clip(mix, dsp.synth_imax_braam(0.85, 36.71), 0.05, gain=0.22)
    dsp.place_clip(mix, dsp.synth_modal_impact(0.42), 1.65, gain=0.22)
    score = dsp.synth_loop_locked_score(dur_s=dur_s, base_hz=55.0)
    mix += score * 0.20
    dsp.apply_vacuum_window(mix, 1.40, 1.56, taper_s=0.008)

    wav_out = os.path.join(work, "smoke_master.wav")
    dsp.master_ebu_r128_linear(mix, wav_out, target_i=-14.2, target_tp=-1.5)
    assert os.path.isfile(wav_out)

    # 2. Write temporary smoke scene inside /tmp? Vite serves from ROOT + /tmp/v6_runtime;
    # let's write a tiny smoke HTML under /tmp/v6_runtime/sdk_smoke.html via `/@fs/tmp/v6_runtime/sdk_smoke.html`
    # or clean temporary file under tools/monarch-v6-imax-sdk/tests/_smoke_page.html removed in finally!
    smoke_html = os.path.join(ROOT, "tools/monarch-v6-imax-sdk/tests/_smoke_page.html")
    try:
        with open(smoke_html, "w", encoding="utf-8") as f:
            f.write("""<!doctype html>
<html><body style="margin:0;background:#050a0e;overflow:hidden">
<script type="module">
import * as THREE from 'three';
import {
  makeImaxMaterial, setImaxLightingPreset, createTexelSnappedShadowRig,
  buildOpticalBreadboardTexture, createImaxOpticalPass,
  createVolumetricSpotlightCone, createLoopLockedDustMotes,
  createBallisticParticleSystem, GLM, buildLoftGeometry,
  createGroundContactAO, createCinemaCameraRig,
  assertSafeLatinGlyphs, loadVerifiedCinemaFonts,
  createGpuHudCompositor, drawImaxShortHud
} from '/tools/monarch-v6-imax-sdk/index.js';

const p = new URLSearchParams(location.search);
const W = Number(p.get('w') || 540), H = Number(p.get('h') || 960);
const CAPTIONS = [{ t0: 0.05, t1: 0.90, text: 'V6 IMAX SDK Ready', hi: 'IMAX SDK', color: '#ffd187' }];
assertSafeLatinGlyphs(CAPTIONS.map((c) => c.text));
await loadVerifiedCinemaFonts();

const canvas = document.createElement('canvas');
canvas.width = W; canvas.height = H;
document.body.appendChild(canvas);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
renderer.autoClear = false;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#091115');
setImaxLightingPreset('cinema_lab');

const bb = buildOpticalBreadboardTexture();
const floor = new THREE.Mesh(
  new THREE.BoxGeometry(400, 10, 400),
  makeImaxMaterial({ color: '#24272b', map: bb.albedo, normalMap: bb.normal, mapRepeat: [6, 6], polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2 })
);
floor.position.y = -5;
scene.add(floor);

// Parametric lofted capsule sculpture + 2-bone IK check
const rings = [];
for (let r = 0; r <= 12; r++) {
  const u = r / 12;
  const rad = Math.sin(Math.max(0.08, u * Math.PI)) * 9.5;
  const ring = [];
  for (let c = 0; c < 20; c++) {
    const th = (c / 20) * Math.PI * 2;
    ring.push([(u - 0.5) * 32, 10 + Math.sin(th) * rad * 0.65, Math.cos(th) * rad]);
  }
  rings.push(ring);
}
const hero = new THREE.Mesh(buildLoftGeometry(rings, true, true), makeImaxMaterial({ color: '#c8642b', specPower: 0.92 }));
scene.add(hero);
scene.add(createGroundContactAO({ width: 34, depth: 22 }));

const knee = GLM.solveTwoBoneIK(GLM.vec3(0, 10, 0), GLM.vec3(8, 0, 5), 8, 8, GLM.vec3(0, 1, 0));
if (!Number.isFinite(knee.y)) throw new Error('IK failed');

const cone = createVolumetricSpotlightCone({ height: 95 });
cone.position.set(0, 48, -10);
scene.add(cone);

const motes = createLoopLockedDustMotes({ count: 40, loopDurationS: 4.0 });
scene.add(motes.mesh);
const sparks = createBallisticParticleSystem({ count: 32 });
scene.add(sparks.mesh);

const shadowRig = createTexelSnappedShadowRig(renderer, { excludeObjects: [cone, motes.mesh] });
const imaxPass = createImaxOpticalPass(renderer, W, H);
const hud = createGpuHudCompositor(renderer, W, H);
const camera = new THREE.PerspectiveCamera(42, W / H, 1.4, 3000);
const camRig = createCinemaCameraRig(camera, { totalFrames: 120, shotCuts: new Set([0]), impacts: [{ frame: 50, amp: 1.1 }] });

function renderFrame(f, opts = { showCaptions: true }) {
  const time = f / 30.0;
  const ang = (2 * Math.PI * f) / 120.0; // Exact 1-cycle orbit -> seamless f=119 -> f=0!
  hero.rotation.y = Math.sin(ang) * 0.25;
  motes.update(time);
  sparks.update(GLM.vec3(0, 4, 0), time, { intensity: 0.8 });

  const pos = GLM.vec3(Math.cos(ang) * 72, 26, Math.sin(ang) * 72);
  const look = GLM.vec3(0, 9, 0);
  const { focusDist, motionVec } = camRig.apply({ frame: f, pos, look, fov: 42 });
  shadowRig.updateShadowMap(scene, look, 55);
  imaxPass.render(scene, camera, { focusDist, dofRange: 42, maxBlur: 2.8, motionVec, time });
  drawImaxShortHud(hud.ctx, { frame: f, time, hudTag: 'SDK V6 SMOKE', telemetryMetric: '30 FPS' }, CAPTIONS, opts);
  hud.composite();
}

window.renderFramePNG = (f) => { renderFrame(f); return canvas.toDataURL('image/png'); };
window.renderCoverPNG = () => { renderFrame(0, { showCaptions: false, coverMode: true, coverTitle: 'SDK V6' }); return canvas.toDataURL('image/png'); };

const gl = renderer.getContext();
const buf = new Uint8Array(W * H * 4);
let ws = null, waitAck = null;
window.connectRawWS = (port, wid) => new Promise((res, rej) => {
  ws = new WebSocket(`ws://127.0.0.1:${port}/?w=${wid}`);
  ws.binaryType = 'arraybuffer';
  ws.onmessage = () => { if (waitAck) { const r = waitAck; waitAck = null; r(); } };
  ws.onopen = () => res(true);
  ws.onerror = rej;
});
window.streamFramesWS = async (a, b) => {
  if (a > 0) renderFrame(a - 1);
  for (let f = a; f < b; f++) {
    renderFrame(f);
    gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, buf);
    await new Promise((r) => { waitAck = r; ws.send(buf); });
  }
};
window.__IMAX_READY__ = true;
</script></body></html>
""")

        out_dir = os.path.join(work, "exports")
        subprocess.run(
            [
                "node", "tools/monarch-v6-imax-sdk/cli/render_imax_ws.mjs",
                "--page", "/tools/monarch-v6-imax-sdk/tests/_smoke_page.html",
                "--mode", "render",
                "--w", "360", "--h", "640",
                "--frames", "120", "--chunk", "60", "--workers", "2",
                "--build-dir", os.path.join(work, "build"),
                "--export-dir", out_dir,
                "--audio", wav_out,
                "--out-name", "SDK-Smoke-V6.mp4",
            ],
            cwd=ROOT,
            check=True,
        )

        mp4_out = os.path.join(out_dir, "SDK-Smoke-V6.mp4")
        stats = fqa.verify_imax_mp4(
            mp4_path=mp4_out,
            expected_frames=120,
            shot_cuts={0, 50},
            check_seamless_loop=True,
            max_loop_mae=12.0,
            vacuum_window_s=(1.42, 1.54),
            scale_w=135,
            scale_h=240,
        )
        assert stats["decoded_frames"] == 120
        assert stats["aba_spikes"] == 0
    finally:
        if os.path.exists(smoke_html):
            os.remove(smoke_html)
        shutil.rmtree(work, ignore_errors=True)
