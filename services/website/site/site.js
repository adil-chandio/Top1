/**
 * Top1 services site — renders everything from config.js
 * Koi dependency nahi, koi build step nahi.
 */

import { CONFIG, FILMS, TIERS, INCLUDED, EXCLUDED, FAQ } from './config.js';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const CURRENCY_SYMBOL = { PKR: 'PKR', USD: '$' };

/**
 * Drive video embed URL.
 * Drive direct MP4 streaming block karta hai, isliye /preview iframe use hota hai.
 * File public hona chahiye: anyone-with-link = reader.
 */
function driveEmbed(id) {
  return `https://drive.google.com/file/d/${id}/preview`;
}

function isDrive(film) {
  return film.provider === 'drive' && film.driveId;
}

function price(key) {
  const value = CONFIG.pricing[key];
  if (!value) return null;
  const symbol = CURRENCY_SYMBOL[CONFIG.currency] ?? CONFIG.currency;
  return `${symbol} ${value.toLocaleString('en-US')}`;
}

/* ─── Contact links ──────────────────────────────────── */

function contactLinks() {
  const links = [];
  if (CONFIG.email) {
    links.push({ label: 'Email', href: `mailto:${CONFIG.email}`, text: CONFIG.email });
  }
  if (CONFIG.whatsapp) {
    const num = String(CONFIG.whatsapp).replace(/[^\d]/g, '');
    links.push({
      label: 'WhatsApp',
      href: `https://wa.me/${num}`,
      text: `+${num}`,
    });
  }
  return links;
}

function renderContacts() {
  const direct = $('#contact-direct');
  const links = contactLinks();

  if (!links.length) {
    direct.innerHTML = `
      <p class="cd-label">Setup needed</p>
      <p style="font-size:.85rem;color:var(--warn);margin:0">
        config.js mein email ya WhatsApp daalo, warna form email client par
        bhejega aur koi reply nahi aayega.
      </p>`;
  } else {
    direct.innerHTML =
      '<p class="cd-label">Or write directly</p>' +
      links.map((l) => `<a href="${l.href}">${l.label} · ${l.text}</a>`).join('');
  }

  const foot = $('#foot-contact');
  foot.innerHTML = links.length
    ? links.map((l) => `<li><a href="${l.href}">${l.label}</a></li>`).join('')
    : '<li><a href="#brief">Send a brief</a></li>';

  const social = $('#foot-social');
  const entries = Object.entries(CONFIG.socials).filter(([, url]) => url);
  social.innerHTML = entries.length
    ? entries
        .map(([k, url]) => `<li><a href="${url}" rel="me noopener" target="_blank">${k[0].toUpperCase() + k.slice(1)}</a></li>`)
        .join('')
    : '<li><a href="#brief">Start a brief</a></li>';
}

/* ─── Hero film ──────────────────────────────────────── */

function renderHero() {
  const film = FILMS.find((f) => f.featured) ?? FILMS[0];
  if (!film) return;

  const figure = $('#hero-film');
  const video = $('#hero-video');
  const playBtn = $('#hero-play');

  // 16:9 hero ko squeeze na kare
  if (film.aspect === '16:9') figure.classList.add('is-wide');

  $('#hero-caption').innerHTML =
    `<strong>${film.title}</strong><span>${film.category} · ${film.duration}</span>`;

  if (isDrive(film)) {
    // Drive: poster dikhao, click par iframe embed
    video.remove();
    const img = document.createElement('img');
    img.src = film.poster;
    img.alt = '';
    img.width = 1080;
    img.height = 1920;
    img.fetchPriority = 'high';
    figure.prepend(img);

    const launch = () => {
      const frame = document.createElement('iframe');
      frame.src = `${driveEmbed(film.driveId)}?autoplay=1`;
      frame.title = film.title;
      frame.allow = 'autoplay; fullscreen; encrypted-media';
      frame.allowFullscreen = true;
      frame.className = 'hero-iframe';
      figure.querySelector('img')?.remove();
      figure.prepend(frame);
      figure.classList.add('is-playing');
    };

    playBtn.addEventListener('click', launch);
    return;
  }

  video.poster = film.poster;
  video.src = film.path;

  const start = () => {
    figure.classList.add('is-playing');
    video.muted = false;
    video.loop = true;
    video.play().catch(() => {
      // Autoplay with sound blocked — fall back to muted
      video.muted = true;
      video.play().catch(() => figure.classList.remove('is-playing'));
    });
  };

  playBtn.addEventListener('click', start);
  video.addEventListener('click', () => {
    if (figure.classList.contains('is-playing')) {
      video.paused ? video.play() : video.pause();
    }
  });
}

/* ─── Film grid ──────────────────────────────────────── */

function renderFilms() {
  const grid = $('#film-grid');
  const lb = $('#lightbox');
  const lbVideo = $('#lb-video');
  const lbTitle = $('#lb-title');

  grid.innerHTML = FILMS.map((film) => {
    const wide = film.aspect === '16:9' ? ' is-wide' : '';
    const source = isDrive(film) ? 'Drive' : '';
    return `
    <button class="card${wide}" type="button" role="listitem"
            data-id="${film.id}" aria-label="Play ${film.title}, ${film.duration}">
      <img src="${film.poster}" alt="" loading="lazy" />
      <span class="card-body">
        <span class="card-cat">${film.category}${source ? ` · ${source}` : ''}</span>
        <h3>${film.title}</h3>
        <span class="card-time">${film.duration} · ${film.aspect}</span>
      </span>
      ${film.featured ? '<span class="card-badge">Featured</span>' : ''}
    </button>`;
  }).join('');

  /** Clean up whatever is currently inside the dialog */
  const resetLightbox = () => {
    lbVideo.pause();
    lbVideo.removeAttribute('src');
    lbVideo.load();
    lbVideo.hidden = false;
    lb.querySelector('iframe')?.remove();
  };

  grid.addEventListener('click', (event) => {
    const card = event.target.closest('.card');
    if (!card) return;
    const film = FILMS.find((f) => f.id === card.dataset.id);
    if (!film) return;

    resetLightbox();
    lbTitle.textContent = `${film.title} · ${film.duration}`;

    if (isDrive(film)) {
      // Drive: iframe embed. 16:9 ho to dialog ko wide karo
      lb.classList.toggle('is-wide', film.aspect === '16:9');
      lbVideo.hidden = true;
      const frame = document.createElement('iframe');
      frame.src = `${driveEmbed(film.driveId)}?autoplay=1`;
      frame.title = film.title;
      frame.allow = 'autoplay; fullscreen; encrypted-media';
      frame.allowFullscreen = true;
      lbVideo.after(frame);
    } else {
      lb.classList.toggle('is-wide', film.aspect === '16:9');
      lbVideo.src = film.path;
      lbVideo.poster = film.poster;
      lbVideo.play().catch(() => {});
    }

    lb.showModal();
  });

  const close = () => {
    resetLightbox();
    lb.close();
  };

  $('#lb-close').addEventListener('click', close);
  lb.addEventListener('click', (e) => {
    // Click on backdrop (dialog itself, not its children)
    if (e.target === lb) close();
  });
  lb.addEventListener('close', resetLightbox);

  $('#p-films').textContent = String(FILMS.length);
}

/* ─── Tiers ──────────────────────────────────────────── */

function renderTiers() {
  const host = $('#tiers');

  host.innerHTML = TIERS.map((tier) => {
    const amount = price(tier.priceKey);
    return `
      <article class="tier${tier.popular ? ' is-popular' : ''}">
        ${tier.popular ? '<span class="tier-tag">Most picked</span>' : ''}
        <h3 class="tier-name">${tier.name}</h3>
        <p class="tier-len">${tier.length}</p>
        <p class="tier-line">${tier.line}</p>
        <p class="tier-price">
          ${amount ?? 'Get a quote'}
          <small>${amount ? 'per film' : 'quoted per project'}</small>
        </p>
        <p class="tier-days">${tier.days} delivery</p>
        <p class="tier-best">${tier.best}</p>
      </article>`;
  }).join('');

  $('#included').innerHTML = INCLUDED.map((i) => `<li>${i}</li>`).join('');
  $('#excluded').innerHTML = EXCLUDED.map((i) => `<li>${i}</li>`).join('');
}

/* ─── FAQ ────────────────────────────────────────────── */

function renderFaq() {
  $('#faq-list').innerHTML = FAQ.map((item, i) => `
    <details${i === 0 ? ' open' : ''}>
      <summary>${item.q}</summary>
      <p>${item.a}</p>
    </details>
  `).join('');
}

/* ─── Workflow ───────────────────────────────────────── */

function renderWorkflow() {
  if (!CONFIG.showWorkflow) return;
  const section = $('#workflow');
  section.hidden = false;

  const steps = [
    'Idea chosen against your niche and past episodes',
    'Original script with a hook and a payoff',
    'Voiceover and word-level caption timing',
    'Frame-locked shot plan',
    '3D assembly and render',
    'QA: decode, loudness, caption bounds',
    'Final files written to your Google Drive',
  ];

  $('#flow-steps').innerHTML = steps.map((s) => `<li>${s}</li>`).join('');
}

/* ─── Brief form ─────────────────────────────────────── */

function briefText(data) {
  return [
    'New 3D video brief',
    '',
    `Topic: ${data.topic}`,
    `Audience: ${data.audience}`,
    `Takeaway: ${data.takeaway}`,
    `Length: ${data.length}`,
    `Language: ${data.language}`,
    `Email: ${data.email}`,
    data.reference ? `Reference: ${data.reference}` : '',
    '',
    `Sent from ${location.href}`,
  ].filter(Boolean).join('\n');
}

function setupBrief() {
  const form = $('#brief-form');
  const status = $('#form-status');
  const button = $('#submit-btn');

  if (CONFIG.formMode === 'none') {
    form.style.display = 'none';
    return;
  }

  const setStatus = (message, isError = false) => {
    status.textContent = message;
    status.classList.toggle('is-error', isError);
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Native validation first
    if (!form.checkValidity()) {
      const firstInvalid = form.querySelector(':invalid');
      firstInvalid?.focus();
      setStatus('Please fill in the required fields.', true);
      return;
    }

    const data = Object.fromEntries(new FormData(form).entries());

    if (CONFIG.formMode === 'mailto') {
      if (!CONFIG.email) {
        setStatus(
          'No email is configured yet. Add CONFIG.email in config.js — the form cannot send anywhere without it.',
          true
        );
        return;
      }
      const subject = encodeURIComponent(`3D video brief — ${data.topic}`.slice(0, 120));
      const body = encodeURIComponent(briefText(data));
      window.location.href = `mailto:${CONFIG.email}?subject=${subject}&body=${body}`;
      setStatus('Opening your email app. Send the draft to finish.');
      return;
    }

    if (CONFIG.formMode === 'formspree') {
      if (!CONFIG.formspree) {
        setStatus('Formspree endpoint missing in config.js.', true);
        return;
      }
      button.disabled = true;
      button.textContent = 'Sending…';
      try {
        const response = await fetch(CONFIG.formspree, {
          method: 'POST',
          headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(String(response.status));
        form.reset();
        setStatus('Brief sent. You will hear back within a day.');
      } catch {
        setStatus(
          `Could not send. Email directly: ${CONFIG.email || 'add an email in config.js'}`,
          true
        );
      } finally {
        button.disabled = false;
        button.textContent = 'Send brief';
      }
    }
  });
}

/* ─── Misc ───────────────────────────────────────────── */

function renderMisc() {
  $('#year').textContent = String(new Date().getFullYear());
  $('#cur-label').textContent = CONFIG.currency;

  if (CONFIG.tagline) {
    document.title = `Top1 — ${CONFIG.tagline}`;
  }

  // Header CTA: WhatsApp if present, else scroll to form
  const headCta = $('#head-cta');
  if (CONFIG.whatsapp) {
    const num = String(CONFIG.whatsapp).replace(/[^\d]/g, '');
    headCta.href = `https://wa.me/${num}`;
    headCta.target = '_blank';
    headCta.rel = 'noopener';
    headCta.textContent = 'WhatsApp';
  }
}

/* ─── Init ───────────────────────────────────────────── */

renderMisc();
renderHero();
renderFilms();
renderTiers();
renderFaq();
renderWorkflow();
renderContacts();
setupBrief();

// Setup warning (sirf dev ke liye, console mein)
if (!CONFIG.email && !CONFIG.whatsapp) {
  console.warn(
    '[Top1] config.js mein email ya WhatsApp set nahi hai. ' +
    'Brief form kisi ko nahi bhejega. services/website/site/config.js kholo.'
  );
}
