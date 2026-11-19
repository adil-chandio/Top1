import { demoAssetName, findDemo } from './demos.js';

export function isPlainClick(event) {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.altKey && !event.shiftKey;
}

function setupFilmNavigation() {
  const rail = document.querySelector('#demo-grid');
  const nav = document.querySelector('#demo-nav');
  const previous = document.querySelector('#demo-prev');
  const next = document.querySelector('#demo-next');
  const firstCard = rail.firstElementChild;

  function sync() {
    const overflow = rail.scrollWidth - rail.clientWidth;
    nav.hidden = overflow < 3;
    previous.disabled = rail.scrollLeft < 3;
    next.disabled = rail.scrollLeft >= overflow - 2;
  }

  function advance(direction) {
    const card = firstCard.getBoundingClientRect().width;
    const gap = Number.parseFloat(getComputedStyle(rail).columnGap) || 0;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    rail.scrollBy({ left: direction * (card + gap), behavior: reduce ? 'auto' : 'smooth' });
  }

  previous.addEventListener('click', () => advance(-1));
  next.addEventListener('click', () => advance(1));
  rail.addEventListener('scroll', sync, { passive: true });
  window.addEventListener('resize', sync);
  sync();
}

function shotTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = (seconds % 60).toFixed(1).replace(/\.0$/, '');
  return `${minutes}:${remainder.padStart(remainder.includes('.') ? 4 : 2, '0')}`;
}

export function initDemoPlayer() {
  const dialog = document.querySelector('#demo-dialog');
  if (!dialog) return;
  setupFilmNavigation();

  const video = document.querySelector('#demo-video');
  const title = document.querySelector('#demo-title');
  const tag = document.querySelector('#demo-tag');
  const description = document.querySelector('#demo-description');
  const length = document.querySelector('#demo-length');
  const close = document.querySelector('#close-demo');
  const loadPrompt = document.querySelector('#demo-viewer-prompt');
  const fileLink = document.querySelector('#demo-file');
  const script = document.querySelector('#demo-script');
  const studio = document.querySelector('#demo-studio');
  const lang = document.querySelector('#demo-lang');
  const quality = document.querySelector('#demo-quality');
  const sound = document.querySelector('#demo-sound');
  const status = document.querySelector('#demo-status');
  const shotGuide = document.querySelector('#demo-shot-guide');
  const shots = document.querySelector('#demo-shots');
  let playback = 0;

  function renderShotGuide(film) {
    shotGuide.open = false;
    shots.replaceChildren(...film.shots.map((shot) => {
      const row = document.createElement('li');
      const button = document.createElement('button');
      button.className = 'shot-jump';
      button.type = 'button';
      button.disabled = true;
      const timestamp = document.createElement('span');
      timestamp.className = 'shot-jump-time';
      timestamp.textContent = shotTime(shot.jumpTo);
      button.append(timestamp, document.createTextNode(shot.shotNote));
      button.addEventListener('click', () => {
        if (video.readyState < 1 || !Number.isFinite(video.duration)) return;
        video.currentTime = Math.min(shot.jumpTo, Math.max(0, video.duration - .05));
        video.scrollIntoView({ block: 'nearest' });
      });
      row.append(button);
      return row;
    }));
  }

  function syncShots() {
    const ready = dialog.open && video.readyState >= 1 && Number.isFinite(video.duration);
    for (const button of shots.querySelectorAll('button')) button.disabled = !ready;
  }

  function syncSound() {
    const playingSound = !video.muted && video.volume > 0;
    sound.setAttribute('aria-pressed', String(playingSound));
    sound.querySelector('use').setAttribute('href', `/icons.svg#${playingSound ? 'volume' : 'volume-off'}`);
    sound.querySelector('span').textContent = playingSound ? 'Sound on' : 'Sound off';
  }

  for (const card of document.querySelectorAll('[data-demo]')) {
    card.addEventListener('click', (event) => {
      if (!isPlainClick(event) || typeof dialog.showModal !== 'function') return;
      const film = findDemo(card.dataset.demo);
      if (!film) return;
      event.preventDefault();
      const request = ++playback;
      title.textContent = film.title;
      tag.textContent = film.voiceLabel ? film.category : `CINEMA CUT ${film.number} / ${film.category}`;
      description.textContent = film.description;
      length.textContent = `${film.duration} SEC`;
      quality.textContent = `${film.width ?? 720}P · 24 FPS`;
      lang.textContent = film.voiceLabel ?? '';
      lang.hidden = !film.voiceLabel;
      script.hidden = !film.sample;
      if (film.sample) script.href = film.sample;
      else script.removeAttribute('href');
      studio.hidden = !film.studio;
      if (film.studio) studio.href = film.studio;
      else studio.removeAttribute('href');
      loadPrompt.dataset.demoPreset = film.id;
      fileLink.href = card.href;
      video.setAttribute('aria-label', film.title);
      video.poster = `/demos/${demoAssetName(film.id, 'webp')}`;
      renderShotGuide(film);
      // This click is a playback gesture; only the narrated film starts unmuted.
      video.muted = !film.voiceLabel;
      status.hidden = true;
      dialog.showModal();
      dialog.scrollTop = 0;
      video.src = card.href;
      syncSound();
      video.play()?.catch(() => {
        if (dialog.open && request === playback && !video.error) {
          status.textContent = 'Tap play to start the film.';
          status.hidden = false;
        }
      });
    });
  }

  video.addEventListener('loadedmetadata', syncShots);
  video.addEventListener('emptied', syncShots);
  video.addEventListener('playing', () => { status.hidden = true; });
  video.addEventListener('volumechange', syncSound);
  video.addEventListener('error', () => {
    if (!dialog.open || !video.hasAttribute('src')) return;
    status.textContent = 'This browser could not load the film. Try opening the MP4 directly.';
    status.hidden = false;
  });
  sound.addEventListener('click', () => {
    const enable = video.muted || video.volume === 0;
    if (enable && video.volume === 0) video.volume = 1;
    video.muted = !enable;
    syncSound();
  });
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    if (dialog.open) return;
    playback++;
    video.pause();
    video.removeAttribute('src');
    video.removeAttribute('poster');
    video.load();
  });
}
