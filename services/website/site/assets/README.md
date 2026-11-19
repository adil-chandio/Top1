# Apni videos yahan daalo

Har film ke liye 2 files:

```
my-film.mp4     1080×1920, H.264, faststart, max 25 MB
my-film.webp    poster thumbnail
```

Poster banane ke liye:
```sh
ffmpeg -ss 26.6 -i my-film.mp4 -frames:v 1 -q:v 80 my-film.webp
```

Phir `../config.js` ke FILMS array mein entry add karo:
```js
{
  id: 'my-film',
  title: 'Film ka naam',
  category: 'Mechanism',
  duration: '24s',
  path: '/assets/my-film.mp4',
  poster: '/assets/my-film.webp',
  aspect: '9:16',
  featured: false,
  line: 'Ek line ka description.',
},
```

Detail: `../../README.md`
