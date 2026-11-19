export const EXAMPLE = Object.freeze({
  topic: 'Phone ki storage full kyun ho jaati hai?',
  language: 'roman-urdu',
  style: 'explainer',
  duration: '25',
});

const languages = {
  'roman-urdu': {
    label: 'Roman Urdu',
    instruction: 'Write the voiceover and captions in natural Roman Urdu using Latin letters. Keep familiar product and interface terms in English where useful. Do not transliterate into Urdu script.',
  },
  english: {
    label: 'English',
    instruction: 'Write the voiceover and captions in conversational English. Use short sentences and avoid jargon.',
  },
};

const styles = {
  explainer: {
    label: 'Explainer',
    opening: 'Open with a visual question or contradiction.',
    middle: 'Explain one idea with a concrete visual example.',
    ending: 'Give one useful takeaway the viewer can act on.',
    guardrail: 'Flag any factual claims that need a source. Do not invent statistics.',
  },
  promo: {
    label: 'Product promo',
    opening: 'Show one problem the audience recognizes.',
    middle: 'Demonstrate a single product benefit with an observable before/after or use case.',
    ending: 'Close with one clear, low-pressure call to action.',
    guardrail: 'If product details are missing, label them as placeholders. Do not invent results, prices, ratings, or guarantees.',
  },
  story: {
    label: 'Mini story',
    opening: 'Start with a character, object, or situation in the middle of a moment.',
    middle: 'Show one change that raises a clear question or tension.',
    ending: 'Resolve the question with one visual payoff.',
    guardrail: 'Clearly label fictional or composite scenes and avoid presenting invented events as fact.',
  },
};

const durations = {
  15: { words: '25–33', beats: ['0–3', '3–11', '11–15'] },
  25: { words: '45–55', beats: ['0–4', '4–18', '18–25'] },
  45: { words: '80–100', beats: ['0–5', '5–34', '34–45'] },
};

function option(options, key, field) {
  if (!Object.hasOwn(options, key)) throw new RangeError(`Choose a valid ${field}.`);
  return options[key];
}

function singleLine(value, field, maxLength) {
  const clean = typeof value === 'string' ? value.trim().replace(/\s+/gu, ' ') : '';
  if (!clean) throw new RangeError(`Enter ${field}.`);
  if (clean.length > maxLength) throw new RangeError(`Keep ${field} under ${maxLength + 1} characters.`);
  return clean;
}

export function buildPrompt({ topic, language, style, duration, visualDirection }) {
  const subject = singleLine(topic, 'a topic', 120);
  const lang = option(languages, language, 'language');
  const format = option(styles, style, 'format');
  const length = option(durations, duration, 'duration');
  const guide = typeof visualDirection === 'string' ? visualDirection.trim() : '';
  const [hookTime, middleTime, endTime] = length.beats;

  return {
    label: `${lang.label} · ${duration} sec · ${format.label}`,
    text: [
      `Plan a ${duration}-second faceless 9:16 ${format.label.toLowerCase()} for Shorts or Reels.`,
      `TOPIC\n${subject}`,
      `LANGUAGE\n${lang.instruction}`,
      'STRUCTURE\n' + [
        `1. Hook (${hookTime}s): ${format.opening}`,
        `2. Main beat (${middleTime}s): ${format.middle}`,
        `3. Payoff (${endTime}s): ${format.ending}`,
      ].join('\n'),
      ...(guide ? [`VISUAL DIRECTION\n${guide}`] : []),
      `RETURN\nA title and a table with one row per beat. Columns: Time, Exact voiceover, On-screen caption (6 words or fewer), Visual direction (subject, framing and motion). Aim for ${length.words} spoken words total. Use shots that don't require a face on camera and leave space for captions.`,
      `CHECK\n${format.guardrail} Add one line on what to verify and what assets to source or make before editing. Return a plan, not a claim that a video was rendered.`,
    ].join('\n\n'),
  };
}

export function buildBrief({ topic, audience, language, duration, notes }) {
  const subject = singleLine(topic, 'a topic or product', 120);
  const viewer = singleLine(audience, 'an audience', 120);
  const lang = option(languages, language, 'language');
  option(durations, duration, 'duration');
  const extra = typeof notes === 'string' ? notes.replace(/\r\n?/g, '\n').trim() : '';
  if (extra.length > 600) throw new RangeError('Keep notes under 601 characters.');

  return [
    'CUSTOM SHORT BLUEPRINT',
    '',
    `Topic or product: ${subject}`,
    `Audience: ${viewer}`,
    `Language: ${lang.label}`,
    `Target: ${duration} seconds, vertical (9:16), faceless`,
    ...(extra ? ['', 'Tone, angle, or takeaway:', extra] : []),
    '',
    'Requested deliverables:',
    '- A hook and exact voiceover script',
    '- A timed shot-by-shot visual plan',
    '- On-screen caption ideas and editable prompts',
    '',
    'Scope: planning documents, not a rendered video. Please confirm price and delivery before starting.',
  ].join('\n');
}
