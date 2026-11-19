/**
 * YAHAN SAB KUCH BADLO. Koi code chhune ki zaroorat nahi.
 *
 * Jab tumhari videos aa jayein:
 *   1. MP4 + WebP ko  assets/  folder mein daalo
 *   2. Neeche FILMS array mein entry add karo
 *   3. Bas. Site khud update ho jayegi.
 */

export const CONFIG = {
  // ─── Brand ────────────────────────────────────────────
  brand: 'top1',
  tagline: '3D films for ideas',

  // ─── Contact — SABSE ZAROORI ──────────────────────────
  // Ye 3 cheezein bharo, warna site par koi order nahi kar sakta.
  email: '',                    // e.g. 'hello@top1.studio'
  whatsapp: '',                 // e.g. '923001234567' (country code, no +, no spaces)
  formspree: '',                // e.g. 'https://formspree.io/f/xxxxxxxx'
                                // Free account: formspree.io — 50 submissions/month

  // Brief form kahan bhejni hai. Options:
  //   'mailto'      → user ka email client khulta hai
  //   'formspree'   → formspree URL se bhejta hai
  //   'none'        → form band, sirf email/WhatsApp dikhega
  formMode: 'mailto',

  // ─── Pricing (PKR) ────────────────────────────────────
  // 0 rakho to "Get a quote" dikhega, price nahi.
  pricing: {
    short: 25000,     // 15 sec
    standard: 45000,  // 30 sec
    deep: 70000,      // 50 sec
  },

  // ─── Currency ─────────────────────────────────────────
  // 'PKR' ya 'USD'
  currency: 'PKR',

  // ─── Socials (khali chhodo to hide ho jata hai) ───────
  socials: {
    instagram: '',
    youtube: '',
    linkedin: '',
    fiverr: '',
    upwork: '',
  },

  // ─── Offer C — sirf tab on karo jab pipeline chal jaye ─
  showWorkflow: false,
};

/**
 * FILMS
 * ─────────────────────────────────────────────────────
 * provider: 'file'  → apni MP4, site/assets/ atha public/demos/ se
 *           'drive' → Google Drive, driveId se embed (koi download nahi)
 * aspect:   '9:16' | '16:9' | '1:1'
 *
 * Drive videos ke liye: sirf driveId + poster ka thumbnail URL.
 * File ko public karna zaroori hai (anyone with link = reader).
 *
 * Apni videos aane par: site/assets/ mein daalo, path '/assets/film.mp4'.
 */
export const FILMS = [
  {
    id: 'gecko',
    title: 'How Does a Gecko Let Go?',
    category: 'Science',
    duration: '62s',
    aspect: '9:16',
    featured: true,
    provider: 'drive',
    driveId: '1ONAFv4Q0Tff74c6UAiIgtEui2RbiqD8G',
    driveId: '1ONAFv4Q0Tff74c6UAiIgtEui2RbiqD8G',
    poster: 'https://drive.google.com/thumbnail?id=1ONAFv4Q0Tff74c6UAiIgtEui2RbiqD8G&sz=w1080',
    line: 'A gecko holds a glass wall with no glue and no suction. Watch the toe peel.',
  },
  {
    id: 'air-crush',
    title: 'Who Crushed the Can?',
    category: 'Mechanism',
    duration: '29s',
    aspect: '9:16',
    featured: false,
    provider: 'drive',
    driveId: '1nHCE1Z9e1ijY27NQBb-F-s9Qkro8btRm',
    poster: 'https://drive.google.com/thumbnail?id=1nHCE1Z9e1ijY27NQBb-F-s9Qkro8btRm&sz=w1080',
    line: 'An aluminium can buckles without anyone squeezing it.',
  },
  {
    id: 'bear',
    title: 'Ancient Bear',
    category: 'Character',
    duration: '100s',
    aspect: '16:9',
    featured: false,
    provider: 'drive',
    driveId: '1FbcyPfHGVK6HclfQUnfqLv5UWvGMAITU',
    driveId: '1FbcyPfHGVK6HclfQUnfqLv5UWvGMAITU',
    poster: 'https://drive.google.com/thumbnail?id=1FbcyPfHGVK6HclfQUnfqLv5UWvGMAITU&sz=w1080',
    line: 'A fully modelled creature in a cinematic 3D sequence.',
  },
  {
    id: 'panama',
    title: 'Panama — Premium Edit',
    category: 'Cinematic',
    duration: '47s',
    aspect: '16:9',
    featured: false,
    provider: 'drive',
    driveId: '1hPD7ffTwfkTvTLds3_zenpX6VWHcyH8O',
    driveId: '1hPD7ffTwfkTvTLds3_zenpX6VWHcyH8O',
    poster: 'https://drive.google.com/thumbnail?id=1hPD7ffTwfkTvTLds3_zenpX6VWHcyH8O&sz=w1080',
    line: 'A premium 3D edit built for a wide frame.',
  },
  {
    id: 'ant',
    title: 'Camera Ant — Opening Pilot',
    category: 'Character',
    duration: '24s',
    aspect: '16:9',
    featured: false,
    provider: 'drive',
    driveId: '13MMMlFq2Dixd2mjThpCBj3na4rV8RH80',
    driveId: '13MMMlFq2Dixd2mjThpCBj3na4rV8RH80',
    poster: 'https://drive.google.com/thumbnail?id=13MMMlFq2Dixd2mjThpCBj3na4rV8RH80&sz=w1080',
    line: 'An insect character pilot with full camera work.',
  },
  {
    id: 'reflector',
    title: 'The Light With No Battery',
    category: 'Optics',
    duration: '50s',
    aspect: '9:16',
    featured: false,
    provider: 'drive',
    driveId: '1KhAISrU99cvF-Ioly2v19hry1tACYrTA',
    poster: 'https://drive.google.com/thumbnail?id=1KhAISrU99cvF-Ioly2v19hry1tACYrTA&sz=w1080',
    line: 'A bicycle reflector looks lit up. It has no power source.',
  },
  {
    id: 'halo',
    title: 'Halo Desk Lamp',
    category: 'Product',
    duration: '10s',
    aspect: '9:16',
    featured: false,
    provider: 'drive',
    driveId: '153-qdpVbrJA-j1jZYhAVjT0D0BzDtPwK',
    poster: 'https://drive.google.com/thumbnail?id=153-qdpVbrJA-j1jZYhAVjT0D0BzDtPwK&sz=w1080',
    line: 'A machined switch, a copper ring, and a warm pool of light.',
  },
  {
    id: 'phone-storage',
    title: 'The Phone Storage Trap',
    category: 'Explainer',
    duration: '11s',
    aspect: '9:16',
    featured: false,
    provider: 'drive',
    driveId: '1-27Y0vgVEvaRnvN-DBHBZGaT9fkqW40T',
    poster: 'https://drive.google.com/thumbnail?id=1-27Y0vgVEvaRnvN-DBHBZGaT9fkqW40T&sz=w1080',
    line: 'Files fill up a phone. A macro lens shows where the space goes.',
  },
  {
    id: 'last-signal',
    title: 'The Last Signal',
    category: 'Story',
    duration: '12s',
    aspect: '9:16',
    featured: false,
    provider: 'drive',
    driveId: '1_Nsv-B12hXiK28kUhR0EpF92i2KKmHzr',
    poster: 'https://drive.google.com/thumbnail?id=1_Nsv-B12hXiK28kUhR0EpF92i2KKmHzr&sz=w1080',
    line: 'A probe sends one last pulse. Something answers.',
  },
];

/** Tier definitions — pricing.CONFIG se price aata hai */
export const TIERS = [
  {
    id: 'short',
    name: 'Short',
    length: '15 seconds',
    days: '5 days',
    priceKey: 'short',
    line: 'One clear mechanism or product reveal.',
    best: 'Hooks, teasers, single-idea posts',
  },
  {
    id: 'standard',
    name: 'Standard',
    length: '30 seconds',
    days: '7 days',
    priceKey: 'standard',
    line: 'The three-beat explainer format.',
    best: 'Most explainers and product films',
    popular: true,
  },
  {
    id: 'deep',
    name: 'Deep',
    length: '50 seconds',
    days: '10 days',
    priceKey: 'deep',
    line: 'A full topic with cutaways and slow replay.',
    best: 'Deep dives that need real evidence',
  },
];

export const INCLUDED = [
  'Original 3D animation — no stock footage, no templates',
  'Script + voiceover in Urdu or English',
  'Captions burned in and as a separate .srt file',
  'Poster image for the thumbnail',
  'QA report: duration, loudness and decode verified',
  'Two rounds of revisions',
];

export const EXCLUDED = [
  'Uploading to YouTube, Instagram or any platform',
  'Views, monetization or subscriber guarantees',
  'Raw 3D project files (available at extra cost)',
  'Borrowed footage, models or music you do not own',
];

export const FAQ = [
  {
    q: 'What exactly do I get?',
    a: 'A finished 1080×1920 MP4 at 24fps, a poster image, a caption file, and a QA report. The QA report lists the duration, loudness and decode check we ran before delivery. Everything is ready to upload — you just publish it.',
  },
  {
    q: 'How is this different from AI video tools?',
    a: 'Those tools assemble clips from stock or generated stills. We model the object and animate the mechanism, then time every cut to the frame. That is why the can actually buckles and the reflector ray actually turns. It takes hours, not seconds — and it does not look mass-produced.',
  },
  {
    q: 'Do you upload the video for me?',
    a: 'No. We deliver the files and you publish them from your own account. That keeps your channel yours, and it means you keep full control of titles, tags and timing.',
  },
  {
    q: 'What do you need from me to start?',
    a: 'The topic, who it is for, the one takeaway you want, and any product photos or brand colours. That is it. If you have a reference video you like, send it — it helps.',
  },
  {
    q: 'How many revisions are included?',
    a: 'Two. One after the script, and one after you see the first render. We ask for the script sign-off and a single still frame before the full render, so problems get caught early instead of at the end.',
  },
  {
    q: 'Can you do 16:9 or square?',
    a: 'Yes. Shoot vertical by default because that is what Shorts and Reels want. A square or landscape version of the same film costs a small extra and adds about a day.',
  },
  {
    q: 'What is your payment process?',
    a: '50% to start, 50% before we hand over the final files. You see a watermarked preview first, so you know what you are paying for. Cancelling before the script is approved gets you a full refund.',
  },
  {
    q: 'Who owns the video?',
    a: 'You do, for commercial use, once it is paid for. We keep the right to show it in our portfolio unless you ask us not to in writing. You cannot resell it as a stock clip or template.',
  },
];
