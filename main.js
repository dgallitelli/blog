// ── Theme Toggle ────────────────────────────────────────
(function () {
    const root = document.documentElement;
    const toggle = document.getElementById('theme-toggle');
    const stored = localStorage.getItem('theme');

    if (stored) root.setAttribute('data-theme', stored);

    if (toggle) {
        toggle.addEventListener('click', () => {
            const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
        });
    }
})();

// ── Render Post Cards on Homepage ───────────────────────
(function () {
    const container = document.getElementById('posts');
    if (!container) return;

    fetch('posts.json')
        .then(r => r.json())
        .then(posts => {
            posts.sort((a, b) => b.date.localeCompare(a.date));
            container.innerHTML = posts.map(post => {
                const date = new Date(post.date + 'T00:00:00');
                const formatted = date.toLocaleDateString('en-US', {
                    year: 'numeric', month: 'short', day: 'numeric'
                });
                const tags = (post.tags || [])
                    .map(t => `<span class="post-tag">${t}</span>`)
                    .join('');
                // Support both flat slugs (/blog/slug/) and nested paths (/blog/series/post/)
                const href = post.path || (post.slug + '/');
                return `
                    <a class="post-card" href="${href}">
                        <div class="post-meta">
                            <span class="post-date">${formatted}</span>
                            <div class="post-tags">${tags}</div>
                        </div>
                        <div class="post-title">${post.title}</div>
                        <div class="post-summary">${post.summary}</div>
                    </a>`;
            }).join('');
        })
        .catch(() => {
            container.innerHTML = '<p style="color:var(--text-muted)">No posts yet.</p>';
        });
})();
