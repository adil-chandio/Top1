import * as THREE from 'three';

/**
 * Monarch V6 Hollywood IMAX Cinema SDK — Verified Binary WOFF2 Font Loader,
 * Latin-1 Tofu Guard, Safe-Zone Mobile HUD & GPU Orthographic Compositor (`fonts_hud_sdk.js`).
 */

/**
 * Throws immediately at startup if any string contains non-Latin-1 symbols (`→`, `↓`, `μ`, `–`, `…`)
 * that render as `□` tofu boxes in `@fontsource/*-latin-*.woff2` subsets!
 */
export function assertSafeLatinGlyphs(strings = [], label = 'HUD/Captions') {
  for (const s of strings) {
    if (!s) continue;
    for (let i = 0; i < s.length; i++) {
      const code = s.charCodeAt(i);
      if (code > 0x00ff) {
        throw new Error(
          `[TofuGuard:${label}] Unsafe non-Latin-1 glyph U+${code.toString(16).toUpperCase()} ('${s[i]}') in "${s}". ` +
          `Use Latin-1 ('x', '×', '°', '·', '%', '...', '-') or draw vector paths!`
        );
      }
    }
  }
}

/**
 * Fetches WOFF2 binaries into JS `FontFace` API and asserts non-zero glyph widths so
 * headless Linux Chromium NEVER silently falls back or skips text!
 */
export async function loadVerifiedCinemaFonts(runtimeRoot = '/@fs/tmp/v6_runtime/node_modules') {
  const fontSpecs = [
    {
      family: 'Space Grotesk',
      url: `${runtimeRoot}/@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2`,
      desc: { style: 'normal', weight: '300 700' },
    },
    {
      family: 'IBM Plex Mono',
      url: `${runtimeRoot}/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2`,
      desc: { style: 'normal', weight: '500' },
    },
    {
      family: 'IBM Plex Mono',
      url: `${runtimeRoot}/@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-600-normal.woff2`,
      desc: { style: 'normal', weight: '600' },
    },
  ];

  for (const sp of fontSpecs) {
    const resp = await fetch(sp.url);
    if (!resp.ok) throw new Error(`Failed to fetch font ${sp.url}: ${resp.status}`);
    const buf = await resp.arrayBuffer();
    const ff = new FontFace(sp.family, buf, sp.desc);
    await ff.load();
    document.fonts.add(ff);
  }
  await document.fonts.ready;

  const probeCtx = document.createElement('canvas').getContext('2d');
  probeCtx.font = '700 44px "Space Grotesk"';
  const sgWidth = probeCtx.measureText('Cinema Probe 900x').width;
  probeCtx.font = '600 18px "IBM Plex Mono"';
  const monoWidth = probeCtx.measureText('TELEMETRY 3.20 MM').width;
  if (sgWidth < 80 || monoWidth < 40) {
    throw new Error(`Font glyph width assertion failed! sg=${sgWidth}, mono=${monoWidth}`);
  }
  return { sgWidth, monoWidth };
}

/**
 * Fullscreen GPU HUD Quad Compositor — composites 2D Canvas typography over ACES 3D frame
 * right before `gl.readPixels` in < 1.5 ms!
 */
export function createGpuHudCompositor(renderer, width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;

  const scene = new THREE.Scene();
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  scene.add(
    new THREE.Mesh(
      new THREE.PlaneGeometry(2, 2),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthTest: false, depthWrite: false })
    )
  );

  function composite() {
    tex.needsUpdate = true;
    renderer.setRenderTarget(null);
    renderer.render(scene, cam);
  }

  return { canvas, ctx, composite };
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

/**
 * Clean Minimalistic YouTube Shorts / Reels Safe-Zone HUD & Caption Renderer (`1080x1920`):
 *   - Top safe zone: y >= 138 px
 *   - Right icon-rail safe zone: x <= 905 px
 *   - Bottom chrome safe zone: y <= 1490 px
 */
export function drawImaxShortHud(ctx, state, captions = [], opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  ctx.clearRect(0, 0, W, H);

  if (opts.coverMode) {
    const topGrad = ctx.createLinearGradient(0, 0, 0, 520);
    topGrad.addColorStop(0, 'rgba(4, 8, 12, 0.82)');
    topGrad.addColorStop(1, 'rgba(4, 8, 12, 0.0)');
    ctx.fillStyle = topGrad;
    ctx.fillRect(0, 0, W, 520);

    ctx.save();
    ctx.textAlign = 'center';
    ctx.font = '700 92px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(0,0,0,0.75)';
    ctx.shadowBlur = 24;
    ctx.fillText(opts.coverTitle || 'IMAX 3D', W / 2, 235);

    if (opts.coverSubtitle) {
      ctx.font = '700 58px "Space Grotesk", sans-serif';
      ctx.fillStyle = '#ffd187';
      ctx.fillText(opts.coverSubtitle, W / 2, 320);
    }
    ctx.restore();
    return;
  }

  const { time = 0, hudTag = '', telemetryMetric = '', alertMode = false, funnelWindow = null } = state;

  // 1. Minimalist Top-Left Telemetry Pill (x=52, y=142)
  if (hudTag) {
    ctx.save();
    ctx.font = '600 18px "IBM Plex Mono", monospace';
    const w1 = ctx.measureText(hudTag).width;
    const w2 = telemetryMetric ? ctx.measureText(telemetryMetric).width + 26 : 0;
    const pillW = Math.min(820, 44 + w1 + w2);
    const pillX = 52, pillY = 142, pillH = 44;

    roundRect(ctx, pillX, pillY, pillW, pillH, 22);
    ctx.fillStyle = 'rgba(7, 12, 16, 0.64)';
    ctx.fill();
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
    ctx.stroke();

    const pulse = 0.65 + 0.35 * Math.sin(time * Math.PI * 4.0);
    ctx.beginPath();
    ctx.arc(pillX + 22, pillY + pillH / 2, 5.0, 0, Math.PI * 2);
    ctx.fillStyle = alertMode ? `rgba(255, 108, 74, ${pulse})` : `rgba(110, 246, 208, ${pulse})`;
    ctx.fill();

    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(236, 244, 248, 0.88)';
    ctx.fillText(hudTag, pillX + 38, pillY + pillH / 2 + 1);

    if (telemetryMetric) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.24)';
      ctx.fillText('·', pillX + 46 + w1, pillY + pillH / 2 + 1);
      ctx.fillStyle = '#ffd187';
      ctx.fillText(telemetryMetric, pillX + 62 + w1, pillY + pillH / 2 + 1);
    }
    ctx.restore();
  }

  // 2. Optional Bottom-Left Related-Video Funnel Pointer (vector downward chevron -> zero tofu risk!)
  if (funnelWindow && state.frame >= funnelWindow.f0 && state.frame <= funnelWindow.f1) {
    const fadeIn = Math.min(1.0, (state.frame - funnelWindow.f0) / 10.0);
    const fadeOut = Math.min(1.0, (funnelWindow.f1 - state.frame) / 8.0);
    const alpha = fadeIn * fadeOut;
    const bob = Math.sin(time * 9.0) * 5.0;

    ctx.save();
    ctx.globalAlpha = alpha;
    const fx = 56, fy = 1418 + bob;
    roundRect(ctx, fx, fy, 470, 58, 29);
    ctx.fillStyle = 'rgba(8, 16, 22, 0.84)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(136, 244, 238, 0.52)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(fx + 30, fy + 29, 16, 0, Math.PI * 2);
    ctx.fillStyle = '#88f4ee';
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(fx + 26, fy + 21);
    ctx.lineTo(fx + 38, fy + 29);
    ctx.lineTo(fx + 26, fy + 37);
    ctx.closePath();
    ctx.fillStyle = '#061015';
    ctx.fill();

    ctx.font = '600 22px "Space Grotesk", sans-serif';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#f4f9fb';
    ctx.fillText(funnelWindow.label || 'FULL 3D BREAKDOWN', fx + 58, fy + 30);

    const ax = fx + 432, ay = fy + 29;
    ctx.beginPath();
    ctx.moveTo(ax - 7, ay - 4);
    ctx.lineTo(ax, ay + 5);
    ctx.lineTo(ax + 7, ay - 4);
    ctx.strokeStyle = '#88f4ee';
    ctx.lineWidth = 2.6;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.restore();
  }

  // 3. Single-Line Frosted-Glass Spring-Pop Caption Pill (x=486, y=1318)
  if (!opts.showCaptions) return;
  const cap = captions.find((c) => time >= c.t0 && time <= c.t1);
  if (!cap) return;

  const dtIn = (time - cap.t0) * 30.0;
  const dtOut = (cap.t1 - time) * 30.0;
  const popScale = dtIn < 5.0 ? (0.92 + 0.08 * (1.0 - Math.pow(1.0 - dtIn / 5.0, 3))) : 1.0;
  const capAlpha = Math.min(1.0, dtIn / 2.5, dtOut / 2.5);

  ctx.save();
  ctx.globalAlpha = capAlpha;
  ctx.translate(486, 1318);
  ctx.scale(popScale, popScale);

  ctx.font = '700 44px "Space Grotesk", sans-serif';
  const fullW = ctx.measureText(cap.text).width;
  const boxW = fullW + 72;
  const boxH = 78;

  ctx.shadowColor = 'rgba(0, 0, 0, 0.55)';
  ctx.shadowBlur = 22;
  ctx.shadowOffsetY = 8;
  roundRect(ctx, -boxW / 2, -boxH / 2, boxW, boxH, 39);
  ctx.fillStyle = 'rgba(7, 11, 16, 0.76)';
  ctx.fill();

  ctx.shadowBlur = 0;
  ctx.shadowOffsetY = 0;
  ctx.lineWidth = 1.4;
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.16)';
  ctx.stroke();

  const hi = cap.hi || '';
  const idx = hi ? cap.text.indexOf(hi) : -1;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  const startX = -fullW / 2;

  if (idx >= 0) {
    const pre = cap.text.slice(0, idx);
    const mid = hi;
    const post = cap.text.slice(idx + mid.length);
    const preW = ctx.measureText(pre).width;
    const midW = ctx.measureText(mid).width;
    if (pre) { ctx.fillStyle = '#f6f9fc'; ctx.fillText(pre, startX, 2); }
    ctx.fillStyle = cap.color || '#ffd187';
    ctx.fillText(mid, startX + preW, 2);
    if (post) { ctx.fillStyle = '#f6f9fc'; ctx.fillText(post, startX + preW + midW, 2); }
  } else {
    ctx.fillStyle = '#f6f9fc';
    ctx.fillText(cap.text, startX, 2);
  }
  ctx.restore();
}
