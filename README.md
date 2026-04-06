# Latent Thoughts

Davide Gallitelli's personal blog, hosted on GitHub Pages at [dgallitelli.github.io/blog](https://dgallitelli.github.io/blog).

## Adding a new post

1. Create a folder for your post: `my-post-slug/index.html`
2. Add an entry to `posts.json` with `title`, `date`, `slug`, `tags`, and `summary`
3. Push to `main` — GitHub Actions deploys automatically

### Flat post (e.g. `/blog/my-post/`)
```json
{ "title": "My Post", "date": "2026-04-06", "slug": "my-post", "tags": ["tag"], "summary": "TL;DR" }
```

### Nested post (e.g. `/blog/series/part-1/`)
```json
{ "title": "Series Part 1", "date": "2026-04-06", "path": "series/part-1/", "tags": ["series"], "summary": "TL;DR" }
```

For nested posts, use `path` instead of `slug` and create the matching directory structure.

## Local preview

Open `index.html` in a browser, or use any static server:
```bash
npx serve .
```
