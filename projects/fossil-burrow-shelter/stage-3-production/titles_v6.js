export function drawHud(ctx, state, opts, W, H) {
  ctx.clearRect(0,0,W,H);
  const t = state.time;
  const showCaptions = opts.showCaptions !== false;
  const coverMode = !!opts.coverMode;

  // cinematic letterbox bars
  ctx.fillStyle = 'rgba(0,0,0,0.88)';
  ctx.fillRect(0,0,W, Math.floor(H*0.055));
  ctx.fillRect(0,Math.floor(H*0.945),W, Math.ceil(H*0.055));

  // subtle vignette in HUD layer for text legibility
  const vg = ctx.createLinearGradient(0,H*0.55,0,H);
  vg.addColorStop(0,'rgba(0,0,0,0)');
  vg.addColorStop(0.65,'rgba(0,0,0,0.10)');
  vg.addColorStop(1,'rgba(0,0,0,0.55)');
  ctx.fillStyle=vg; ctx.fillRect(0,Math.floor(H*0.55),W,Math.floor(H*0.45));

  // captions
  const captions = [
    {s:0.10,e:2.9,txt:'A 250-MILLION-YEAR-OLD\nBURROW', style:'big'},
    {s:3.0,e:5.1,txt:'TWO SPECIES.\nONE SHELTER.', style:'big'},
    {s:5.2,e:8.2,txt:'NOT A PREDATOR TRAP', style:'mid'},
    {s:8.25,e:11.1,txt:'THE AMPHIBIAN\nWAS INJURED', style:'big'},
    {s:11.2,e:16.1,txt:'HEALED BONE MARKS\nPROVE IT SURVIVED', style:'mid'},
    {s:16.2,e:20.0,txt:'IT ENTERED ALIVE', style:'big'},
    {s:20.0,e:23.1,txt:'RESTED. THEN LEFT.', style:'big'},
    {s:23.2,e:27.4,txt:'A FLASH FLOOD\nBURIED THEM TOGETHER', style:'big'},
    {s:27.5,e:31.5,txt:'NOT VIOLENCE.\nSHELTER.', style:'impact'},
  ];

  if (showCaptions && !coverMode) {
    for (const c of captions) {
      if (t < c.s || t > c.e) continue;
      const p = (t-c.s)/(c.e-c.s);
      const fadeIn = Math.min(1, (t-c.s)/0.12);
      const fadeOut = Math.min(1, (c.e-t)/0.15);
      const alpha = Math.max(0, Math.min(fadeIn, fadeOut));
      const punch = p < 0.08 ? (1 + (0.08-p)*2.5) : 1;
      const yBase = c.style==='impact' ? H*0.50 : H*0.80;
      drawCaption(ctx, c.txt, W/2, yBase, alpha, punch, c.style, W);
    }
  }

  if (coverMode || (t < 2.5)) {
    const a = coverMode ? 1 : Math.max(0, 1 - Math.max(0,(t-1.8)/0.7));
    ctx.save(); ctx.globalAlpha=a;
    ctx.textAlign='center'; ctx.fillStyle='#F4EFE6';
    ctx.font='700 86px "Space Grotesk"';
    ctx.fillText('THE FOSSIL', W/2, H*0.18);
    ctx.fillText('BURROW', W/2, H*0.235);
    ctx.font='600 34px "IBM Plex Mono"'; ctx.fillStyle='#FFB35C';
    ctx.fillText('250 MILLION YEARS • ONE SHELTER', W/2, H*0.285);
    ctx.restore();
  }

  // tiny watermark / grade marker
  ctx.save(); ctx.globalAlpha=0.28; ctx.fillStyle='#fff';
  ctx.font='600 18px "IBM Plex Mono"'; ctx.textAlign='left';
  ctx.fillText('TOP1 / IMAX-SHORT', 42, H*0.965);
  ctx.restore();
}

function drawCaption(ctx, text, cx, cy, alpha, punch, style, W) {
  const lines = text.split('\n');
  const size = style==='impact' ? 84 : style==='big' ? 72 : 56;
  const lh = size * 1.12;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(cx, cy);
  ctx.scale(punch, punch);
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.font=`700 ${size}px "Space Grotesk"`;
  for (let i=0;i<lines.length;i++) {
    const y = (i - (lines.length-1)/2) * lh;
    const line = lines[i];
    ctx.lineJoin='round'; ctx.miterLimit=2;
    ctx.strokeStyle='rgba(0,0,0,0.95)'; ctx.lineWidth = style==='impact'?16:12;
    ctx.strokeText(line, 0, y);
    ctx.strokeStyle='rgba(255,90,40,0.28)'; ctx.lineWidth = style==='impact'?24:18;
    ctx.strokeText(line, 0, y);
    ctx.fillStyle = style==='impact' ? '#FFF3D8' : '#FFFFFF';
    ctx.fillText(line, 0, y);
  }
  ctx.restore();
}
