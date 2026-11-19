#!/usr/bin/env node
/**
 * Standalone dev server for the services site.
 *
 * Chalane ka tareeqa:
 *   node services/website/serve.mjs
 *   node services/website/serve.mjs --port 4173
 *
 * Ye main site (Vite) ko chhoota nahi. Apna alag server, alag port.
 * Video files public/demos/ se serve hoti hain taake maujooda films
 * dikh sakein — read-only, kuch change nahi hota.
 */

import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import {
  extname,
  isAbsolute,
  join,
  normalize,
  relative,
  resolve,
  sep,
} from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../..', import.meta.url)));
const siteDir = resolve(fileURLToPath(new URL('./site', import.meta.url)));

const args = process.argv.slice(2);
const portArg = args.indexOf('--port');
const PORT = portArg >= 0 ? Number(args[portArg + 1]) : Number(process.env.PORT || 4173);
const HOST = '0.0.0.0';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.mp4': 'video/mp4',
  '.webp': 'image/webp',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
};

/** Allowed roots: site dir + public (read-only video access) */
const READ_ROOTS = [siteDir, join(root, 'public')];

/**
 * Safely check that `target` really lives inside `base`.
 * NOTE: slicing strings here is wrong — `/a/b`.slice(`/a/c`.length) looks
 * like it starts with "/" even when the two paths are unrelated.
 */
function isInside(base, target) {
  const rel = relative(base, target);
  return rel === '' || (!rel.startsWith('..') && !isAbsolute(rel));
}

function resolvePath(urlPath) {
  let clean;
  try {
    clean = decodeURIComponent(urlPath.split('?')[0]);
  } catch {
    return null; // malformed percent-encoding
  }

  // Normalise and refuse anything that escapes via ..
  const relative = normalize(clean).replace(/^(\.\.[/\\])+/, '').replace(/^[/\\]+/, '');

  const candidates = [
    { base: siteDir, file: join(siteDir, relative) },
    { base: root, file: join(root, relative) },
  ];

  for (const { base, file } of candidates) {
    if (!isInside(base, file)) continue;
    // Repo root is only readable for whitelisted subfolders
    if (base === root && !READ_ROOTS.some((allowed) => isInside(allowed, file))) continue;
    if (!existsSync(file)) continue;

    const stat = statSync(file);
    if (stat.isDirectory()) {
      const index = join(file, 'index.html');
      if (existsSync(index)) return index;
      continue;
    }
    return file;
  }

  return null;
}

const server = createServer((request, response) => {
  const url = request.url || '/';

  // Root / → site/index.html
  const target =
    url === '/' || url === ''
      ? join(siteDir, 'index.html')
      : resolvePath(url);

  if (!target) {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    response.end('404 — not found');
    return;
  }

  const stat = statSync(target);
  const type = MIME[extname(target).toLowerCase()] ?? 'application/octet-stream';

  // Range support for video seeking
  const range = request.headers.range;
  if (range && stat.size) {
    const match = /bytes=(\d*)-(\d*)/.exec(range);
    if (match) {
      const start = match[1] ? Number(match[1]) : 0;
      const end = match[2] ? Number(match[2]) : stat.size - 1;
      if (start >= stat.size) {
        response.writeHead(416, { 'Content-Range': `bytes */${stat.size}` });
        response.end();
        return;
      }
      response.writeHead(206, {
        'Content-Type': type,
        'Content-Range': `bytes ${start}-${end}/${stat.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': end - start + 1,
        'Cache-Control': 'public, max-age=3600',
      });
      createReadStream(target, { start, end }).pipe(response);
      return;
    }
  }

  response.writeHead(200, {
    'Content-Type': type,
    'Content-Length': stat.size,
    'Accept-Ranges': 'bytes',
    'Cache-Control': type.startsWith('video/') ? 'public, max-age=3600' : 'no-cache',
  });

  if (request.method === 'HEAD') {
    response.end();
    return;
  }

  createReadStream(target).pipe(response);
});

server.listen(PORT, HOST, () => {
  console.log(`\n  Top1 services site`);
  console.log(`  ─────────────────────────────────────`);
  console.log(`  http://localhost:${PORT}`);
  console.log(`  ${siteDir}`);
  console.log(`\n  Videos: public/demos/ (read-only)`);
  console.log(`  Config: services/website/site/config.js\n`);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
process.on('SIGINT', () => server.close(() => process.exit(0)));
