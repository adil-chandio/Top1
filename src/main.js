import './styles.css';
import './demos.css';
import { initDemoPlayer, isPlainClick } from './demo-player.js';
import { findDemo } from './demos.js';
import { buildBrief, buildPrompt, EXAMPLE } from './prompts.js';

function formValues(form) {
  return Object.fromEntries(new FormData(form));
}

function focusSection(element) {
  element.scrollIntoView({ block: 'start' });
}

async function copyText(textarea, button, status, successMessage) {
  const text = textarea.value;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = successMessage;
    return;
  } catch {
    // Some embedded or mobile browsers do not grant the async clipboard API.
    textarea.focus({ preventScroll: true });
    textarea.select();
    textarea.setSelectionRange(0, text.length);
    let copied = false;
    try {
      copied = document.execCommand('copy');
    } catch {
      // The selection remains available for manual copying.
    }
    if (copied) button.focus({ preventScroll: true });
    status.textContent = copied ? successMessage : 'Text selected. Use your device’s Copy action.';
  }
}

function downloadText(text, filename) {
  if (!text) return;
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

function reportInvalid(input, message) {
  input.setCustomValidity(message);
  input.reportValidity();
}

function initBuilder() {
  const form = document.querySelector('#prompt-form');
  if (!form) return;

  const topic = form.elements.topic;
  const promptText = document.querySelector('#prompt-text');
  const promptMeta = document.querySelector('#prompt-meta');
  const promptStatus = document.querySelector('#prompt-status');
  const copy = document.querySelector('#copy-prompt');
  const save = document.querySelector('#download-prompt');
  const panel = document.querySelector('#prompt-output');
  const presetBox = document.querySelector('#demo-preset-note');
  const presetLabel = document.querySelector('#demo-preset-label');
  let demoLook;

  function setLook(film) {
    demoLook = film;
    presetBox.hidden = !film;
    presetLabel.textContent = film ? `3D look: ${film.title}` : '';
  }

  function renderPrompt(values, message) {
    const result = buildPrompt({ ...values, visualDirection: demoLook?.preset.visualDirection });
    promptText.value = result.text;
    promptText.scrollTop = 0;
    promptMeta.textContent = result.label;
    promptStatus.textContent = message;
    copy.disabled = save.disabled = false;
  }

  function loadPrompt(values, message) {
    for (const key of ['topic', 'language', 'style', 'duration']) form.elements[key].value = values[key];
    topic.setCustomValidity('');
    renderPrompt(values, message);
  }

  const linkedFilm = findDemo(new URLSearchParams(window.location.search).get('demo'));
  if (linkedFilm) {
    setLook(linkedFilm);
    loadPrompt(linkedFilm.preset, '3D demo prompt loaded. Copy it or make it your own.');
  } else {
    renderPrompt(EXAMPLE, 'Paste it into your AI chat to make the shot plan.');
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const values = formValues(form);
    if (!values.topic.trim()) {
      reportInvalid(topic, 'Enter a topic.');
      return;
    }
    renderPrompt(values, 'Prompt updated. Copy it into your AI chat.');
    if (window.matchMedia('(max-width: 760px)').matches) focusSection(panel);
  });

  form.addEventListener('input', () => {
    topic.setCustomValidity('');
    copy.disabled = save.disabled = true;
    promptStatus.textContent = 'Settings changed. Build again to update this prompt.';
  });

  for (const chip of form.querySelectorAll('[data-topic]')) {
    chip.addEventListener('click', () => {
      setLook(undefined);
      topic.value = chip.dataset.topic;
      topic.setCustomValidity('');
      renderPrompt(formValues(form), 'Example prompt ready to copy.');
    });
  }

  document.querySelector('#use-sample').addEventListener('click', (event) => {
    if (!isPlainClick(event)) return;
    setLook(undefined);
    loadPrompt(EXAMPLE, 'Sample loaded. Edit the topic to make it yours.');
  });
  for (const link of document.querySelectorAll('[data-demo-preset]')) {
    link.addEventListener('click', (event) => {
      if (!isPlainClick(event)) return;
      const film = findDemo(link.dataset.demoPreset);
      if (!film) return;
      const dialog = document.querySelector('#demo-dialog');
      if (dialog?.open) dialog.close();
      setLook(film);
      loadPrompt(film.preset, '3D demo prompt loaded. Copy it or make it your own.');
      // Keep focus with the newly loaded prompt after the anchor scrolls.
      requestAnimationFrame(() => document.querySelector('#builder-title').focus({ preventScroll: true }));
    });
  }
  document.querySelector('#clear-demo-preset').addEventListener('click', () => {
    setLook(undefined);
    form.requestSubmit();
  });

  copy.addEventListener('click', () => copyText(promptText, copy, promptStatus, 'Prompt copied. Paste it into your AI chat.'));
  save.addEventListener('click', () => downloadText(promptText.value, 'top1-short-prompt.txt'));
}

function initBrief() {
  const dialog = document.querySelector('#brief-dialog');
  if (!dialog) return;

  const form = document.querySelector('#brief-form');
  const result = document.querySelector('#brief-result');
  const text = document.querySelector('#brief-text');
  const status = document.querySelector('#brief-status');
  const copy = document.querySelector('#copy-brief');
  const save = document.querySelector('#download-brief');

  document.querySelector('#open-brief').addEventListener('click', () => dialog.showModal());
  document.querySelector('#close-brief').addEventListener('click', () => dialog.close());
  form.addEventListener('input', (event) => {
    event.target.setCustomValidity('');
    if (!result.hidden) {
      copy.disabled = save.disabled = true;
      status.textContent = 'Details changed. Build the brief again to update it.';
    }
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const values = formValues(form);
    if (!values.topic.trim()) return reportInvalid(form.elements.topic, 'Enter a topic or product.');
    if (!values.audience.trim()) return reportInvalid(form.elements.audience, 'Enter an audience.');
    text.value = buildBrief(values);
    text.scrollTop = 0;
    result.hidden = false;
    copy.disabled = save.disabled = false;
    status.textContent = 'Your brief is ready. Nothing has been sent.';
    focusSection(result);
  });

  copy.addEventListener('click', () => copyText(text, copy, status, 'Brief copied. Nothing has been sent.'));
  save.addEventListener('click', () => downloadText(text.value, 'top1-custom-brief.txt'));
}

initBuilder();
initBrief();
initDemoPlayer();
