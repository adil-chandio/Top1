# Deploy — free, no card, no domain

Both the site and the films are now in places that cost nothing.

## What changed so it could be free

The site briefly depended on 39 MB of MP4s in `public/demos/` — outside the site
folder. That meant every deploy had to ship large video files, which is what
makes free hosts unhappy and slow.

All nine films now live in the public Google Drive folder
`1xdVBLKSzKWUdasQDZ6DZeVuF6LwCZON8` instead, and the site is **72 KB** with no
media in it at all. The films stream from Drive, so the host only ever serves
four text files.

| Film | Drive ID |
|---|---|
| How Does a Gecko Let Go? | `1ONAFv4Q0Tff74c6UAiIgtEui2RbiqD8G` |
| Who Crushed the Can? | `1nHCE1Z9e1ijY27NQBb-F-s9Qkro8btRm` |
| Ancient Bear | `1FbcyPfHGVK6HclfQUnfqLv5UWvGMAITU` |
| Panama — Premium Edit | `1hPD7ffTwfkTvTLds3_zenpX6VWHcyH8O` |
| Camera Ant — Opening Pilot | `13MMMlFq2Dixd2mjThpCBj3na4rV8RH80` |
| The Light With No Battery | `1KhAISrU99cvF-Ioly2v19hry1tACYrTA` |
| Halo Desk Lamp | `153-qdpVbrJA-j1jZYhAVjT0D0BzDtPwK` |
| The Phone Storage Trap | `1-27Y0vgVEvaRnvN-DBHBZGaT9fkqW40T` |
| The Last Signal | `1_Nsv-B12hXiK28kUhR0EpF92i2KKmHzr` |

## GitHub Pages (the free host)

The workflow is already in the repo:
`.github/workflows/deploy-services-site.yml`

It runs the site's tests, copies only `services/website/site/` into the artefact,
and publishes it. If tests fail, nothing ships.

**The one thing a token cannot do:** turning Pages on for the first time needs
repo admin, and the automation token is not an admin. So click this once:

**https://github.com/adil-chandio/Top1/settings/pages**
→ **Source: GitHub Actions**

Then the workflow redeploys on every push to `main`.

Live URL: **https://adil-chandio.github.io/Top1/**

### Why the URL has `/Top1/` in it

Pages serves a project repo from a subpath. That is why every URL in the site is
relative — `./site.css`, `./site.js`, `#work`. Never change these to `/site.css`.
If you ever want a clean root URL, the repo itself has to be named
`adil-chandio.github.io`, which means moving this repo. Not worth it yet.

## Vercel

A project already exists (`top1-3d-services`, root `services/website/site`,
framework "Other", no build command). It could not be deployed from here: the
connector's `create_deployment` drops the `projectSettings` object the Vercel API
requires for a project that has never been deployed, so every attempt returns
`The projectSettings object is required for new projects`.

That is a connector bug, not a site problem. To deploy from the Vercel dashboard
instead: import `adil-chandio/Top1` → root directory `services/website/site` →
framework "Other" → empty build command → output `.`.

Vercel is worth doing only if you later get a domain. Pages is enough until then.

## Adding a new film

1. Upload the MP4 to the Drive folder.
2. Right-click → Share → "Anyone with the link" → Viewer.
3. Copy the ID from `https://drive.google.com/file/d/<ID>/view`.
4. Add one entry to `FILMS` in `services/website/site/config.js`:

```js
{
  id: 'my-film',
  title: 'My Film',
  category: 'Product',
  duration: '30s',
  aspect: '16:9',
  featured: false,
  provider: 'drive',
  driveId: 'PASTE_ID_HERE',
  poster: 'https://drive.google.com/thumbnail?id=PASTE_ID_HERE&sz=w1080',
  line: 'One line about it.',
},
```

5. Push. The workflow tests, then deploys.

Run `node services/website/site.test.mjs` before pushing — it checks every film
has a `driveId`, a matching poster URL, and a valid aspect ratio.
