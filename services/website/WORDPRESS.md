# WordPress build — adilchandio4.wordpress.com

The same 3D services offer, published on the free WordPress.com site.
Free plan: no plugins, no custom CSS, no custom JS. Everything below is inline
styles inside page content — the only lever the plan gives us.

## Live pages

| Page | ID | URL |
|---|---|---|
| 3D Video Services | 9 | https://adilchandio4.wordpress.com/3d-video-services/ |
| Work | 11 | https://adilchandio4.wordpress.com/work/ |
| About | 1 | https://adilchandio4.wordpress.com/about/ |

Draft test page `_sanitize-test` (id 6) and the default post (id 3) are deleted.

## What the WordPress.com sanitizer allows

Tested directly against this site, not guessed.

| Thing | Result |
|---|---|
| Inline `style="..."` on any tag | survives |
| `<img>` | survives |
| `<table>` | survives |
| `<ul>` / `<ol>` / `<li>` | survives (but see `wpautop` below) |
| `<iframe>` (Drive preview) | **stripped** |
| `<style>` / `<script>` | **stripped** |
| CSS `background-image` in a style attribute | **stripped** |
| Bare YouTube URL | auto-embeds into a player |
| Bare Drive URL | renders as a plain link only |
| `<!-- wp:html -->` block wrapper | does not help — Drive iframe still stripped |

So: no embedded players on WordPress. Film cards are clickable thumbnails that
open in Google Drive, which is the honest fallback.

## The `wpautop` trap

`wpautop` rewrites the content on save and inserts stray `</p>` tags. Two things
trigger it:

1. An `<img>` immediately followed by a `<div>` on the next line → `</p>` gets
   injected after the `<img>`, breaking the card layout.
2. A `<div>` nested inside an `<a>` → the `<a>` gets split.

**The pattern that works** — put the whole thing on one line, inside a `<p>`:

```html
<div style="flex:1 1 260px;border:1px solid #e5e2dc;border-radius:14px;overflow:hidden">
<p style="margin:0;line-height:0"><a href="DRIVE_VIEW_URL"><img src="THUMB_URL" alt="TITLE" style="width:100%;height:300px;object-fit:cover;display:block;margin:0;border:0"></a></p>
<div style="padding:14px">
<p style="font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#b56a00;margin:0 0 4px">CATEGORY · 9:16 · 62s</p>
<p style="margin:0 0 6px"><a href="DRIVE_VIEW_URL" style="text-decoration:none;color:#111;font-weight:600;font-size:15px">TITLE</a></p>
<p style="font-size:13px;color:#666;line-height:1.5;margin:0">One line about the film.</p>
</div>
</div>
```

Rules that keep it clean:

- One block-level HTML element per line. Never let `wpautop` find whitespace
  between an `<img>` and a `<div>`.
- Every `<a>` gets its own `<p>`.
- Never nest a `<div>` inside an `<a>`.
- No empty lines inside a flex container.
- `<br>` is fine and comes back as `<br />`.

## Thumbnails

Drive thumbnails work as `<img src>`:

```
https://drive.google.com/thumbnail?id=FILE_ID&sz=w800
```

`sz=w800` for wide cards, `sz=w600` for vertical. In the page content the `&`
must be written as `&amp;`.

## Limits we cannot fix on the free plan

- No embedded video player. Click-through to Drive is the only option.
- No dark full-bleed hero. The dark block is a rounded card inside the theme's
  content column, not a page-wide section.
- No sticky nav, no custom fonts, no hover states beyond what inline styles give.
- No checkout. Email is the conversion path:
  `mailto:alipvip19@gmail.com?subject=3D%20video%20brief`

## Homepage

The connector has no site-settings tool, so the front page is still the blog
index. To make the offer the homepage, set it manually once:

**My Site → Settings → Reading → Your homepage displays → A static page →
Homepage: "3D Video Services"**

Same screen: set **Posts page** to a blank page, or leave it.

## Navigation

Add the three pages to the menu manually: **Appearance → Menus → add
"3D Video Services", "Work", "About"**.

## Pricing on the WordPress pages

25,000 / 45,000 / 70,000 PKR — Short 15 s / Standard 30 s / Deep 50 s.
Kept in sync by hand with `site/config.js`. If prices change there, they must be
changed here too.
