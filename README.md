# auto-llms-txt

Make any personal website machine-readable for LLMs and AI agents. A daily GitHub Action traverses your sitemap, scrapes each page, and publishes a `llms.txt` + a human-friendly landing page to GitHub Pages. Zero maintenance after setup.

## How It Works

```
yoursite.com/llms.txt  (301 redirect from your host)
  -> yourusername.github.io/auto-llms-txt/llms.txt  (rebuilt daily)
```

1. GitHub Actions runs at 6 AM UTC, fetches your sitemap, and scrapes each page
2. `llms.txt` and `llms-full.txt` are committed to `data/` (only if content changed)
3. A landing page + both text files deploy to GitHub Pages
4. Your site's `/llms.txt` 301-redirects to GitHub Pages so it stays current automatically

## Live Example

This repo powers [philjohnstonii.com](https://philjohnstonii.com)'s LLM layer:

| File | Description |
|---|---|
| [`/llms.txt`](https://eusef.github.io/auto-llms-txt/llms.txt) | Concise page index — titles, URLs, descriptions |
| [`/llms-full.txt`](https://eusef.github.io/auto-llms-txt/llms-full.txt) | Full content of every page |
| [`/`](https://eusef.github.io/auto-llms-txt/) | Human-friendly landing page |

## Project Structure

```
your-repo/
├── config.json                  # Your site URL and metadata — edit this
├── scraper/
│   ├── scrape.py                # Sitemap-driven scraper (no customization needed)
│   └── requirements.txt
├── docs/
│   └── index.html               # Landing page (auto-populated from llms.txt)
├── data/                        # Generated output (committed by the workflow)
│   ├── llms.txt
│   └── llms-full.txt
└── .github/workflows/
    └── scrape.yml               # Daily scrape + GitHub Pages deployment
```

## Deploy Your Own

### 1. Fork this repo

Fork on GitHub. You can rename it to anything.

### 2. Edit `config.json`

```json
{
  "website_url": "https://yoursite.com",
  "site_name": "Your Name",
  "description": "One-line description of you and what you do",
  "exclude_patterns": [
    "/llms",
    "/cdn-cgi",
    "/cart",
    "/checkout",
    "/search"
  ]
}
```

That's the only file you need to edit. The scraper discovers all pages via your sitemap automatically.

### 3. Enable GitHub Pages

Settings > Pages > Source: **GitHub Actions**

### 4. Run the workflow

Actions > "Scrape Website & Deploy" > Run workflow

After it completes, your files will be live at:
```
https://<you>.github.io/<repo>/llms.txt
https://<you>.github.io/<repo>/llms-full.txt
https://<you>.github.io/<repo>/
```

### 5. Add redirects on your website

Make `yoursite.com/llms.txt` point to the GitHub Pages version. LLMs don't execute JavaScript, so these must be server-side 301 redirects.

**Squarespace**

Settings > Advanced > URL Mappings:
```
/llms.txt -> https://<you>.github.io/<repo>/llms.txt 301
/llms-full.txt -> https://<you>.github.io/<repo>/llms-full.txt 301
```

**WordPress** — add to `functions.php` or use a redirect plugin:
```php
add_action('template_redirect', function() {
    $map = [
        '/llms.txt'      => 'https://<you>.github.io/<repo>/llms.txt',
        '/llms-full.txt' => 'https://<you>.github.io/<repo>/llms-full.txt',
    ];
    if (isset($map[$_SERVER['REQUEST_URI']])) {
        wp_redirect($map[$_SERVER['REQUEST_URI']], 301);
        exit;
    }
});
```

**Netlify** — add a `_redirects` file to your site root:
```
/llms.txt      https://<you>.github.io/<repo>/llms.txt      301!
/llms-full.txt https://<you>.github.io/<repo>/llms-full.txt 301!
```

**Vercel** — add to `vercel.json`:
```json
{
  "redirects": [
    { "source": "/llms.txt",      "destination": "https://<you>.github.io/<repo>/llms.txt",      "permanent": true },
    { "source": "/llms-full.txt", "destination": "https://<you>.github.io/<repo>/llms-full.txt", "permanent": true }
  ]
}
```

**Cloudflare Pages** — add a `_redirects` file:
```
/llms.txt      https://<you>.github.io/<repo>/llms.txt      301
/llms-full.txt https://<you>.github.io/<repo>/llms-full.txt 301
```

**Nginx**
```nginx
location = /llms.txt      { return 301 https://<you>.github.io/<repo>/llms.txt; }
location = /llms-full.txt { return 301 https://<you>.github.io/<repo>/llms-full.txt; }
```

**Apache** — add to `.htaccess`:
```
Redirect 301 /llms.txt      https://<you>.github.io/<repo>/llms.txt
Redirect 301 /llms-full.txt https://<you>.github.io/<repo>/llms-full.txt
```

**No redirect support** — if your host can't do server-side redirects, copy `data/llms.txt` into your site's root directly. You'll lose the auto-update, but the content will be correct until you update it manually.

## Customizing `exclude_patterns`

The scraper skips any URL containing a string in `exclude_patterns`. Use this to filter out pages that aren't useful for LLMs:

```json
"exclude_patterns": [
  "/blog",        // exact path — excludes /blog listing but keeps /blog/post-slug
  "/home",        // exact path — skip a duplicate home/splash page
  "/cdn-cgi/",    // trailing slash = prefix match — excludes /cdn-cgi/anything
  "/tag/",        // prefix match — excludes all tag archive pages
  "/category/",   // prefix match — excludes all category archive pages
  "/cart",        // exact path
  "/checkout",
  "/search",
  "?s="           // no leading slash = substring match against the full URL
]
```

**Pattern matching rules:**

| Pattern | Matches |
|---|---|
| `"/blog"` | Only `yoursite.com/blog` — not `yoursite.com/blog/post` |
| `"/cdn-cgi/"` | `yoursite.com/cdn-cgi/` and anything beneath it |
| `"?s="` | Any URL containing `?s=` (substring match) |

The scraper also automatically skips image/PDF/asset URLs, query strings, and known non-content paths (`/feed`, `/rss`, `/admin`, etc.).

## Adjusting the schedule

The workflow runs at 6 AM UTC by default. Edit `.github/workflows/scrape.yml` to change it:

```yaml
schedule:
  - cron: '0 6 * * *'   # 6 AM UTC daily
```

[Crontab Guru](https://crontab.guru) is useful for building cron expressions.

## Requirements

- Public GitHub repository (GitHub Pages is free for public repos)
- Your website must have a `sitemap.xml` (most CMS platforms generate one automatically)
- No tokens or secrets required

## Cost

$0. GitHub Actions free tier covers the daily cron. GitHub Pages is free for public repos.

## License

MIT
