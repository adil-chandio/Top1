import { isPlainClick } from '../src/demo-player.js';

// The page works as plain links without JS. Enhance only taps, and request
// video bytes on demand so the studio can open on a mobile connection.
export function mountScreening(film) {
  const mp4 = `/demos/${film.asset}.mp4`;
  const { shots } = film;
  const screen = document.querySelector('#screening');
  const cover = document.querySelector('#studio-cover');
  const video = document.querySelector('#studio-video');
  const note = document.querySelector('#playback-note');
  const list = document.querySelector('#chapter-list');
  let pendingSeek = null;
  let requestId = 0;
  let activeIndex = -1;

  function textSpan(className, text) {
    const span = document.createElement('span');
    span.className = className;
    span.textContent = text;
    return span;
  }

  function timecode(seconds) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}:${(seconds % 60).toFixed(2).padStart(5, '0')}`;
  }

  for (const [index, shot] of shots.entries()) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.className = 'chapter-link';
    link.href = `${mp4}#t=${shot.jumpTo}`;
    link.dataset.studioShot = index;
    link.append(textSpan('chapter-index', String(index + 1).padStart(2, '0')), textSpan('timecode', timecode(shot.jumpTo)), textSpan('chapter-label', shot.shotNote));
    item.append(link);
    list.append(item);
  }

  const chapterLinks = document.querySelectorAll('[data-studio-shot]');
  document.querySelector('#shot-count').textContent = `· ${shots.length}`;
  document.querySelector('#all-shots').hidden = false;

  function syncShot() {
    const index = shots.findLastIndex(({ at }) => at <= (pendingSeek ?? video.currentTime));
    if (index === activeIndex) return;
    activeIndex = index;
    for (const link of chapterLinks) {
      if (Number(link.dataset.studioShot) === index) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    }
  }

  function seekWhenReady() {
    if (pendingSeek === null || video.readyState < 1 || !Number.isFinite(video.duration)) return;
    video.currentTime = Math.min(pendingSeek, Math.max(0, video.duration - .04));
    pendingSeek = null;
  }

  function showNote(text) {
    note.textContent = text;
    note.hidden = false;
  }

  function playFrom(at) {
    const request = ++requestId;
    pendingSeek = at;
    note.hidden = true;
    cover.hidden = true;
    video.hidden = false;
    if (!video.hasAttribute('src') || video.error) video.src = mp4;
    seekWhenReady();
    syncShot();
    // Start from the tap itself; loadedmetadata handles a seek on first load.
    video.play()?.catch(() => {
      if (request === requestId && !video.error) showNote('Tap play in the film to start.');
    });
    video.focus({ preventScroll: true });
    screen.scrollIntoView({ block: 'nearest' });
  }

  for (const link of [...document.querySelectorAll('[data-studio-play]'), ...chapterLinks]) {
    link.addEventListener('click', (event) => {
      if (!isPlainClick(event)) return;
      const shot = shots[link.dataset.studioShot];
      event.preventDefault();
      playFrom(shot?.jumpTo ?? 0);
    });
  }

  video.addEventListener('loadedmetadata', seekWhenReady);
  video.addEventListener('seeking', syncShot);
  video.addEventListener('timeupdate', syncShot);
  video.addEventListener('playing', () => { note.hidden = true; });
  video.addEventListener('error', () => showNote('The film could not load here. Use Save MP4 to watch it on your device.'));
}
