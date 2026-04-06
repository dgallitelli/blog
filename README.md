# Latent Thoughts

Davide Gallitelli's personal blog, built with [Hugo](https://gohugo.io) and hosted on [GitHub Pages](https://dgallitelli.github.io/blog/).

## Adding a new post

1. Create a folder under `content/posts/` (or any section): `content/posts/my-post/index.md`
2. Add frontmatter with `title`, `date`, `tags`, and `summary`
3. Push to `main` — GitHub Actions builds and deploys automatically

For a series, add `series: "Series Name"` to frontmatter — posts with the same series name get linked navigation.

## Local preview

```bash
hugo server -D
```
