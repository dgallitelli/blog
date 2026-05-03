# Latent Thoughts — Personal Blog

Personal blog by Davide Gallitelli. Built with Hugo and a custom theme, deployed to GitHub Pages via GitHub Actions.

**Live site:** https://dgallitelli.github.io/blog/

## What This Repo Is

A Hugo-based personal blog. There is no application code, no backend, no database. The entire site is static HTML generated from Markdown content and Go HTML templates.

**Do not** introduce build tools (webpack, npm, etc.), CSS preprocessors, JavaScript frameworks, or server-side logic. The simplicity is intentional.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Static site generator | [Hugo](https://gohugo.io) (extended, v0.147.6 in CI) |
| Theme | Custom `latent` theme (in `themes/latent/`) |
| Styling | Plain CSS with CSS custom properties for dark/light theming |
| Fonts | Instrument Serif (headings), Geist (body), Geist Mono / JetBrains Mono (code) — loaded from Google Fonts |
| Diagrams | Mermaid (lazy-loaded via CDN when a `mermaid` code block is used) |
| Charts | Plotly.js (loaded when frontmatter has `plotly: true`) |
| Hosting | GitHub Pages |
| CI/CD | GitHub Actions (`.github/workflows/hugo.yaml`) — builds on push to `main`, deploys automatically |

## Repository Layout

```
blog/
├── hugo.yaml                  # Site config (title, theme, params, markup settings)
├── content/                   # All blog content (Markdown + images)
│   ├── _index.md              # Homepage title
│   ├── posts/                 # Standalone posts
│   │   └── <slug>/index.md   # Page-bundle post (co-locate images/scripts)
│   ├── autoresearch-week/     # Series: Autoresearch Week (5 parts)
│   ├── llm-wiki-week/         # Series: LLM Wiki Week (3 parts)
│   └── platform-engineering-ai-agents/  # Series: Platform Engineering for AI Agents (3 parts)
├── static/                    # Static assets (logo.svg, og-image.png)
├── themes/latent/             # Custom Hugo theme
│   ├── assets/css/style.css   # All styles (dark/light themes, layout, typography)
│   ├── layouts/
│   │   ├── _default/baseof.html    # Base HTML shell
│   │   ├── _default/single.html    # Single post template (with series nav)
│   │   ├── _default/list.html      # Section list template
│   │   ├── index.html              # Homepage (search, post cards)
│   │   ├── 404.html                # 404 page
│   │   ├── partials/head.html      # <head> (meta, OG tags, fonts, CSS, conditional Plotly)
│   │   ├── partials/header.html    # Sticky header with nav + theme toggle
│   │   ├── partials/footer.html    # Footer + Mermaid init + theme toggle JS
│   │   ├── shortcodes/plotly.html  # {{< plotly >}} shortcode for interactive charts
│   │   └── _default/_markup/render-codeblock-mermaid.html  # Mermaid code-block renderer
├── public/                    # Hugo build output (gitignored)
└── .github/workflows/hugo.yaml  # CI: build + deploy to GitHub Pages
```

## Content Tasks

Most work in this repo is writing or editing blog posts.

### Creating a new post

1. Create a page bundle: `content/<section>/<slug>/index.md`
2. Include all required frontmatter fields:
   ```yaml
   ---
   title: "Post Title"
   date: YYYY-MM-DD
   tags: ["tag1", "tag2"]
   summary: "One-line description for the homepage card."
   ---
   ```
3. Optional frontmatter: `series`, `plotly`, `hidden`
4. Co-locate images in the same folder or an `images/` subfolder
5. Use relative paths for co-located assets: `![alt](images/diagram.png)`

### Creating a new series

1. Create the section: `content/my-series/_index.md` with `hidden: true`
2. Add posts as sub-bundles with matching `series: "Series Name"` frontmatter
3. The theme auto-generates a numbered series nav from posts sorted by `date` ascending

### Diagrams

- Use fenced `mermaid` code blocks — the theme handles rendering via CDN
- Do not add `<script>` tags for Mermaid manually; the footer partial loads it conditionally

### Interactive charts

- Set `plotly: true` in frontmatter to load Plotly.js
- Use the `{{< plotly json="path/to/chart.json" >}}` shortcode
- Store chart JSON files alongside the post in the page bundle

## Theme Tasks

The custom theme lives in `themes/latent/`. Key rules:

### CSS

- **Single file:** `themes/latent/assets/css/style.css` — all styles are here
- **Theming via custom properties:** colors are defined in `[data-theme="dark"]` and `[data-theme="light"]` blocks. When changing colors, update both themes
- **No CSS preprocessor.** Keep it as plain CSS
- **Max width is `780px`** (`--max-width`) — the blog is a single-column reading layout

### Templates

- `baseof.html` is the HTML shell — partials are composed here
- `single.html` renders individual posts (includes series navigation)
- `index.html` is the homepage (post cards + client-side search)
- `list.html` is the section listing (used by series `_index.md` pages, but these are typically hidden)

### Adding a new shortcode

Place it in `themes/latent/layouts/shortcodes/<name>.html`. Reference the existing `plotly.html` shortcode for patterns.

### JavaScript

- All JS is inline in templates (no external JS files, no bundler)
- Theme toggle logic lives in `partials/footer.html`
- Homepage search lives in `index.html`
- Keep JS minimal and vanilla — no frameworks

## CI/CD

The GitHub Actions workflow (`.github/workflows/hugo.yaml`) builds and deploys on push to `main`.

- Hugo extended v0.147.6
- Builds with `--gc --minify`
- Deploys to GitHub Pages

**Do not** change the Hugo version without verifying theme compatibility. The `extended` variant is required for CSS processing.

## Development

```bash
# Local preview (with drafts)
hugo server -D

# Build for production
hugo build --gc --minify
```

## Conventions

- Commit messages are imperative, concise, and describe the visible change (e.g., "Add search bar to homepage with keyboard shortcut")
- Content uses page bundles (`index.md` inside a named folder) so images and scripts are co-located
- Series use `_index.md` with `hidden: true` at the section level
- The theme is dark-first (`data-theme="dark"` default on `<html>`) with light mode via toggle
- All CSS uses custom properties defined in `:root` / `[data-theme]` blocks — no CSS preprocessor
- No JavaScript frameworks — vanilla JS only (search filter, theme toggle, Mermaid/Plotly loading)

## Common Pitfalls

| Pitfall | Guidance |
|---------|----------|
| Editing `public/` | Never. This is the build output directory and is gitignored |
| Adding `<script>` tags in content | Use shortcodes or code-block renderers instead |
| Forgetting `summary` in frontmatter | The homepage card will show no description |
| Using absolute paths for co-located images | Use relative paths within the page bundle |
| Breaking dark/light theme parity | When editing CSS colors, always update both `[data-theme]` blocks |
| Adding npm/node dependencies | This is a pure Hugo site — no Node.js in the build chain |

## File Quick Reference

| I want to... | Edit this file |
|--------------|----------------|
| Write/edit a blog post | `content/<section>/<slug>/index.md` |
| Change site metadata | `hugo.yaml` |
| Modify the HTML structure | `themes/latent/layouts/_default/baseof.html` |
| Change how a single post renders | `themes/latent/layouts/_default/single.html` |
| Change the homepage | `themes/latent/layouts/index.html` |
| Edit styles | `themes/latent/assets/css/style.css` |
| Update `<head>` / meta tags | `themes/latent/layouts/partials/head.html` |
| Change header navigation | `themes/latent/layouts/partials/header.html` |
| Modify footer or Mermaid config | `themes/latent/layouts/partials/footer.html` |
| Add a new shortcode | `themes/latent/layouts/shortcodes/<name>.html` |
| Change CI/CD | `.github/workflows/hugo.yaml` |
