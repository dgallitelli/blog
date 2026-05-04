# Author byline chip — design

**Date:** 2026-05-04
**Status:** Approved, ready for implementation

## Problem

Each blog post used to close with an italic bio paragraph ("Davide Gallitelli is a..."). The bio was inconsistent across posts (France vs. ASEAN, "Specialist SA" vs. "Senior Specialist SA") and felt like boilerplate. Those closing lines have already been removed. We now need a cleaner, consistent, site-wide way to attribute each post to its author.

## Goals

- Consistent author attribution on every post, driven by one source of truth
- Fits the existing editorial aesthetic (eyebrow → title → metadata → content)
- Zero per-post frontmatter changes — new posts inherit automatically
- No added build tooling, no JS framework, no preprocessor

## Non-goals

- An `/about` page on the blog (the header already links to an external about site; keeping that as-is)
- Social links, publication lists, or an extended bio card
- Making the byline clickable
- Per-post author overrides (single-author blog)

## Design

A compact byline line sits between the post `<h1>` and the existing `.post-meta` row. It contains a small circular avatar followed by the author name — no "By" prefix, no role, no link.

**Visual hierarchy (post header, top to bottom):**

1. `.post-eyebrow` — series name or "Essay" (unchanged)
2. `<h1>` — post title (unchanged)
3. `.post-byline` — **new**: avatar + name
4. `.post-meta` — date · reading time · tags (unchanged)

## Implementation

### Template change

File: `themes/latent/layouts/_default/single.html`

Insert a new `.post-byline` block between the `<h1>` (line 7) and the `.post-meta` div (line 8). The author name is pulled from `.Site.Params.author`, which is already set to `"Davide Gallitelli"` in `hugo.yaml`. The avatar URL is hotlinked from GitHub.

```html
<div class="post-byline">
    <img class="post-byline-avatar"
         src="https://github.com/dgallitelli.png?size=56"
         alt="{{ .Site.Params.author }}"
         width="28" height="28"
         loading="lazy"
         referrerpolicy="no-referrer">
    <span class="post-byline-name">{{ .Site.Params.author }}</span>
</div>
```

Notes:
- `width`/`height` attributes prevent layout shift
- `referrerpolicy="no-referrer"` avoids leaking referrer to GitHub
- `loading="lazy"` is a safe no-op for above-the-fold images but matches the theme's minimalism
- `?size=56` serves a 2x image for retina (displayed at 28px)

### CSS change

File: `themes/latent/assets/css/style.css`

Add a new `.post-byline` block alongside the existing `.post-header` / `.post-meta` rules. Use existing CSS custom properties so dark/light themes are inherited automatically.

```css
.post-byline {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    margin-top: 0.75rem;
    margin-bottom: 0.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
}

.post-byline-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 1px solid var(--border);
    object-fit: cover;
    display: block;
}

.post-byline-name {
    font-weight: 500;
    color: var(--text);
}
```

The byline uses the same `--text-muted` family of colors as `.post-meta` so it reads as part of the header block. The name itself uses `--text` for slightly more weight than surrounding metadata.

### Data source

- Author name: `.Site.Params.author` from `hugo.yaml` — already present (`author: "Davide Gallitelli"`)
- Avatar: `https://github.com/dgallitelli.png?size=56` (hardcoded in template; this is site-owner identity, not content)

No changes to `hugo.yaml`, frontmatter, or content files.

## What we considered and rejected

- **Hosting the avatar in `static/`** — rejected per user preference for hotlinked GitHub avatar (auto-updates when GH photo changes; no file to maintain)
- **Making the byline clickable to an /about page** — rejected; kept as pure byline
- **Role text ("Senior AI Specialist SA")** — rejected; keeps the chip minimal
- **Putting the chip inside `.post-meta`** — rejected; crowds the meta row on posts with many tags
- **Putting the chip at the bottom of the post** — rejected; that's effectively what the removed bio was doing

## Verification

1. `hugo server -D` runs without errors
2. Byline renders on one sample post per top-level section:
   - `posts/` (e.g., `agentcore-runtime-vs-harness-vs-openai`)
   - `world-models-series/` (e.g., `part2-jepa-deep-dive`)
   - `autoresearch-week/`
   - `llm-wiki-week/`
   - `platform-engineering-ai-agents/`
3. Dark theme: avatar border, name, and spacing read correctly
4. Light theme: same
5. Mobile width (~375px): chip does not overflow; wraps naturally
6. Screenshot via chrome-devtools MCP (headless) captured for desktop dark, desktop light, and mobile dark

## Out of scope (for follow-up)

- Extended author card with social links
- An in-blog `/about` page replacing the external user site
- Per-post author overrides (guest posts)
