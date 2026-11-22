/**
 * Monarch Cam #03 — V6 Hollywood IMAX Minimalist Mobile HUD, Action Graphics & Safe-Zone Captions!
 *
 * Strictly honors YouTube Shorts / Reels / TikTok 1080x1920 Safe Zones:
 *   - Top Safe Zone: y >= 138 px
 *   - Right Action-Rail Safe Zone: x <= 905 px
 *   - Bottom Scrub/Title Safe Zone: y <= 1490 px
 *   - Single-line frosted obsidian-glass caption pill at y = 1320 (max 1-4 punchy words,
 *     dynamic spring pop-in, subtle specular border, color-coded scientific keyword highlight!)
 */

export const SHORT_CAPTIONS_V6 = [
  { t0:  0.04, t1:  1.16, text: 'under 2 pennies',       hi: '2 pennies',      color: '#ffd187' },
  { t0:  1.24, t1:  2.42, text: '50× body length/s',     hi: '50×',            color: '#ffd187' },
  { t0:  2.54, t1:  3.48, text: '12.5 mm tall...',       hi: '12.5 mm',        color: '#88f4ee' },
  { t0:  3.54, t1:  4.50, text: 'into a 3.2 mm gap',     hi: '3.2 mm',         color: '#ffd187' },
  { t0:  4.56, t1:  5.36, text: 'nearly 4× shorter',     hi: '4× shorter',     color: '#88f4ee' },
  { t0:  5.42, t1:  6.36, text: 'zero bones.',           hi: 'zero bones.',    color: '#ff9b73' },
  { t0:  6.44, t1:  7.82, text: 'UC Berkeley X-ray:',    hi: 'X-ray:',         color: '#88f4ee' },
  { t0:  7.88, t1:  9.36, text: 'shingle plates slide',  hi: 'plates slide',   color: '#ffd187' },
  { t0:  9.42, t1: 10.35, text: 'squeezing 60% flat',    hi: '60% flat',       color: '#6ef6c8' },
  { t0: 10.55, t1: 11.18, text: 'Wait.',                 hi: 'Wait.',          color: '#ff7b54' },
  { t0: 11.24, t1: 12.76, text: 'arms past 80°?',        hi: 'past 80°?',      color: '#ffd187' },
  { t0: 12.82, t1: 14.12, text: 'shoulders collapse.',   hi: 'collapse.',      color: '#ff6e4a' },
  { t0: 14.20, t1: 16.22, text: 'every foot lifts off',  hi: 'lifts off',      color: '#88f4ee' },
  { t0: 16.30, t1: 17.34, text: 'Zero feet down.',       hi: 'Zero feet',      color: '#6ef6c8' },
  { t0: 17.40, t1: 18.88, text: 'curved spines claw',    hi: 'spines claw',    color: '#ffd187' },
  { t0: 18.94, t1: 20.32, text: 'like twin oars',        hi: 'twin oars',      color: '#88f4ee' },
  { t0: 20.38, t1: 22.64, text: '900× body weight',      hi: '900×',           color: '#ffd187' },
  { t0: 22.72, t1: 24.16, text: 'still sprints away',    hi: 'sprints away',   color: '#6ef6c8' },
  { t0: 24.24, t1: 26.20, text: 'spines need grip:',     hi: 'need grip:',     color: '#ffd187' },
  { t0: 26.28, t1: 28.00, text: 'slick floors spin out', hi: 'spin out',       color: '#88f4ee' },
  { t0: 28.08, t1: 30.30, text: 'coarse grit snags',     hi: 'grit snags',     color: '#ff8a5c' },
  { t0: 30.38, t1: 31.82, text: '4 in 5 fail at 3.2 mm', hi: '4 in 5 fail',    color: '#ff7b54' },
  { t0: 31.88, t1: 33.14, text: 'turning or wedging',    hi: 'wedging',        color: '#ffd187' },
  { t0: 33.22, t1: 34.22, text: 'Tap full breakdown',    hi: 'full breakdown', color: '#88f4ee' },
  { t0: 34.26, t1: 34.97, text: 'to see how it...',      hi: 'how it...',      color: '#ffd187' },
];

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

export function drawShortHudV6(ctx, state, opts = { showCaptions: true }) {
  const W = ctx.canvas.width;
  const H = ctx.canvas.height;
  ctx.clearRect(0, 0, W, H);

  if (opts.coverMode) {
    drawCoverArtworkOverlay(ctx, W, H);
    return;
  }

  const { time, shot, telemetryMetric } = state;

  // =========================================================================
  // 1. MINIMALIST IMAX OPTICAL TELEMETRY PILL (TOP-LEFT SAFE ZONE: x=54, y=144)
  // =========================================================================
  ctx.save();
  const topLabel = shot.hudTag;
  const metricText = telemetryMetric || '';
  ctx.font = '600 18px "IBM Plex Mono", monospace';
  const w1 = ctx.measureText(topLabel).width;
  const w2 = metricText ? ctx.measureText(metricText).width + 26 : 0;
  const pillW = Math.min(820, 44 + w1 + w2);
  const pillX = 52;
  const pillY = 142;
  const pillH = 44;

  roundRect(ctx, pillX, pillY, pillW, pillH, 22);
  ctx.fillStyle = 'rgba(7, 12, 16, 0.64)';
  ctx.fill();
  ctx.lineWidth = 1.2;
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
  ctx.stroke();

  // Pulsing live cinema recording indicator dot
  const pulse = 0.65 + 0.35 * Math.sin(time * Math.PI * 4.0);
  ctx.beginPath();
  ctx.arc(pillX + 22, pillY + pillH / 2, 5.0, 0, Math.PI * 2);
  ctx.fillStyle = shot.id === 'S4A_PUSHUP' || shot.id === 'S7B_GATE_FAIL'
    ? `rgba(255, 108, 74, ${pulse})`
    : `rgba(110, 246, 208, ${pulse})`;
  ctx.fill();

  ctx.textBaseline = 'middle';
  ctx.fillStyle = 'rgba(236, 244, 248, 0.88)';
  ctx.fillText(topLabel, pillX + 38, pillY + pillH / 2 + 1);

  if (metricText) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.24)';
    ctx.fillText('·', pillX + 46 + w1, pillY + pillH / 2 + 1);
    ctx.fillStyle = '#ffd187';
    ctx.fillText(metricText, pillX + 62 + w1, pillY + pillH / 2 + 1);
  }
  ctx.restore();

  // =========================================================================
  // 2. BESPOKE ACTION-GRAPHICS MICRO-BADGES ON KEY SCIENTIFIC IMPACTS!
  // =========================================================================
  // Beat S6 Hydraulic Slam Peak Callout (f=634..680)
  if (state.frame >= 634 && state.frame <= 680) {
    const pop = Math.min(1.0, (state.frame - 634) / 6.0);
    ctx.save();
    ctx.translate(W * 0.46, 365);
    ctx.scale(0.92 + 0.08 * pop, 0.92 + 0.08 * pop);
    roundRect(ctx, -185, -34, 370, 68, 16);
    ctx.fillStyle = 'rgba(14, 10, 6, 0.76)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 209, 135, 0.55)';
    ctx.lineWidth = 1.6;
    ctx.stroke();
    ctx.font = '700 28px "Space Grotesk", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffd187';
    ctx.fillText('896× BODY WEIGHT · 6.08 N', 0, 1);
    ctx.restore();
  }

  // =========================================================================
  // 3. YOUTUBE SHORTS RELATED-VIDEO FUNNEL POINTER (f=955..1035, bottom-left safe zone!)
  // =========================================================================
  if (state.frame >= 955 && state.frame <= 1036) {
    const fadeIn = Math.min(1.0, (state.frame - 955) / 10.0);
    const fadeOut = Math.min(1.0, (1036 - state.frame) / 8.0);
    const alpha = fadeIn * fadeOut;
    const bob = Math.sin(time * 9.0) * 5.0;

    ctx.save();
    ctx.globalAlpha = alpha;
    const fx = 56;
    const fy = 1418 + bob;
    roundRect(ctx, fx, fy, 470, 58, 29);
    ctx.fillStyle = 'rgba(8, 16, 22, 0.84)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(136, 244, 238, 0.52)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Play triangle badge
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
    ctx.fillText('FULL 5-MIN 3D BREAKDOWN', fx + 58, fy + 30);

    // Crisp vector downward chevron (zero Unicode subset risk!)
    const ax = fx + 432;
    const ay = fy + 29;
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

  // =========================================================================
  // 4. ULTRA-CLEAN MINIMALIST FROSTED-GLASS CAPTION PILL (y = 1315, x centered at 490!)
  // =========================================================================
  if (!opts.showCaptions) return;

  const cap = SHORT_CAPTIONS_V6.find((c) => time >= c.t0 && time <= c.t1);
  if (!cap) return;

  const dtIn = (time - cap.t0) * 30.0;
  const dtOut = (cap.t1 - time) * 30.0;
  const popScale = dtIn < 5.0 ? (0.92 + 0.08 * (1.0 - Math.pow(1.0 - dtIn / 5.0, 3))) : 1.0;
  const capAlpha = Math.min(1.0, dtIn / 2.5, dtOut / 2.5);

  ctx.save();
  ctx.globalAlpha = capAlpha;
  // Slightly left of dead-center (x = 486) so right edge NEVER touches YouTube Shorts' right icon column!
  const cx = 486;
  const cy = 1318;
  ctx.translate(cx, cy);
  ctx.scale(popScale, popScale);

  ctx.font = '700 44px "Space Grotesk", sans-serif';
  const fullW = ctx.measureText(cap.text).width;
  const padX = 36;
  const boxW = fullW + padX * 2;
  const boxH = 78;

  // Soft drop shadow + frosted obsidian capsule
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

  // Render crisp white text with colored keyword highlight!
  const idx = cap.text.indexOf(cap.hi);
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  const startX = -fullW / 2;

  if (idx >= 0) {
    const pre = cap.text.slice(0, idx);
    const mid = cap.hi;
    const post = cap.text.slice(idx + mid.length);
    const preW = ctx.measureText(pre).width;
    const midW = ctx.measureText(mid).width;

    if (pre) {
      ctx.fillStyle = '#f6f9fc';
      ctx.fillText(pre, startX, 2);
    }
    ctx.fillStyle = cap.color;
    ctx.fillText(mid, startX + preW, 2);
    if (post) {
      ctx.fillStyle = '#f6f9fc';
      ctx.fillText(post, startX + preW + midW, 2);
    }
  } else {
    ctx.fillStyle = '#f6f9fc';
    ctx.fillText(cap.text, startX, 2);
  }
  ctx.restore();
}

function drawCoverArtworkOverlay(ctx, W, H) {
  ctx.save();
  // Subtle top & bottom cinema gradient for instant mobile readability
  const topGrad = ctx.createLinearGradient(0, 0, 0, 520);
  topGrad.addColorStop(0, 'rgba(4, 8, 12, 0.82)');
  topGrad.addColorStop(1, 'rgba(4, 8, 12, 0.0)');
  ctx.fillStyle = topGrad;
  ctx.fillRect(0, 0, W, 520);

  ctx.textAlign = 'center';
  ctx.font = '700 96px "Space Grotesk", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.shadowColor = 'rgba(0,0,0,0.75)';
  ctx.shadowBlur = 24;
  ctx.fillText('3.2 MM GAP', W / 2, 235);

  ctx.font = '700 62px "Space Grotesk", sans-serif';
  ctx.fillStyle = '#ffd187';
  ctx.fillText('900× BODY WEIGHT', W / 2, 322);
  ctx.restore();
}
