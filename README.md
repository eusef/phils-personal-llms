# LLM-Discoverable Personal API

Make any personal website machine-readable for LLMs and AI agents. No servers to run, no accounts beyond GitHub, no manual updates after initial setup.

A daily GitHub Action scrapes your website, outputs structured JSON, and deploys everything to GitHub Pages. Your website 301-redirects `/llms.txt` to the GitHub Pages version, so content stays in sync automatically. Works with Squarespace, WordPress, Wix, Hugo, Jekyll, or any site you can scrape.

## How It Works

```
yoursite.com/llms.txt (301 redirect from your host)
  -> yourusername.github.io/your-repo/llms.txt (auto-updated daily)
     -> yourusername.github.io/your-repo/api/profile.json
     -> yourusername.github.io/your-repo/api/resume.json
     -> yourusername.github.io/your-repo/api/blog.json
```

1. A GitHub Action scrapes your website daily at 6 AM UTC
2. Structured JSON is committed to `data/` (only if content changed)
3. GitHub Pages serves those files as a public, zero-auth API
4. `llms.txt` on your domain 301-redirects to the GitHub Pages version

## Live Example

This repo powers [philjohnstonii.com](https://philjohnstonii.com)'s LLM layer:

| Endpoint | Description |
|---|---|
| [`/api/profile.json`](https://eusef.github.io/phils-personal-llms/api/profile.json) | Bio, roles, location, contact |
| [`/api/resume.json`](https://eusef.github.io/phils-personal-llms/api/resume.json) | Career timeline, skills, differentiators |
| [`/api/blog.json`](https://eusef.github.io/phils-personal-llms/api/blog.json) | All blog posts with excerpts and full content |
| [`/llms.txt`](https://eusef.github.io/phils-personal-llms/llms.txt) | Standard llms.txt with full inline profile |
| [`/llms-full.txt`](https://eusef.github.io/phils-personal-llms/llms-full.txt) | Extended profile for direct LLM consumption |

## Project Structure

```
your-repo/
├── data/                        # Scraped JSON (auto-updated by GitHub Action)
│   ├── profile.json
│   ├── resume.json
│   └── blog.json
├── scraper/
│   ├── scrape.py                # Python scraper (customize for your site)
│   └── requirements.txt
├── docs/
│   └── index.html               # GitHub Pages landing page
├── .github/workflows/
│   └── scrape.yml               # Daily scrape + Pages deployment
├── llms.txt                     # Standard llms.txt (deployed to Pages)
├── llms-full.txt                # Extended version with full content
└── PLAYBOOK.md                  # Step-by-step guide for your own site
```

## Deploy Your Own

See [PLAYBOOK.md](PLAYBOOK.md) for the full walkthrough.

Quick version:

1. Fork this repo
2. Update `scraper/scrape.py` for your site's URL and page structure
3. Enable GitHub Pages (Settings > Pages > Source: GitHub Actions)
4. Run the workflow (Actions > "Scrape Website & Deploy" > Run workflow)
5. Add 301 redirects on your website (see platform instructions below)
6. Verify at `https://<you>.github.io/<repo>/api/profile.json`

### Setting Up Redirects by Platform

The key step is making `yoursite.com/llms.txt` redirect to the GitHub Pages version. LLM crawlers don't execute JavaScript, so server-side (301) redirects are required.

**Squarespace**
Settings > Advanced > URL Mappings (or Settings > Developer Tools > URL Mappings), then add:
```
/llms.txt -> https://<you>.github.io/<repo>/llms.txt 301
/llms-full.txt -> https://<you>.github.io/<repo>/llms-full.txt 301
```

**WordPress**
Add to your theme's `functions.php` or use a redirect plugin:
```php
add_action('template_redirect', function() {
    if ($_SERVER['REQUEST_URI'] === '/llms.txt') {
        wp_redirect('https://<you>.github.io/<repo>/llms.txt', 301);
        exit;
    }
    if ($_SERVER['REQUEST_URI'] === '/llms-full.txt') {
        wp_redirect('https://<you>.github.io/<repo>/llms-full.txt', 301);
        exit;
    }
});
```
Or with `.htaccess` (Apache):
```
Redirect 301 /llms.txt https://<you>.github.io/<repo>/llms.txt
Redirect 301 /llms-full.txt https://<you>.github.io/<repo>/llms-full.txt
```

**Wix**
Dashboard > SEO Tools > URL Redirect Manager, then add 301 redirects for both paths.

**Netlify**
Add a `_redirects` file to your site root:
```
/llms.txt https://<you>.github.io/<repo>/llms.txt 301!
/llms-full.txt https://<you>.github.io/<repo>/llms-full.txt 301!
```

**Vercel**
Add to `vercel.json`:
```json
{
  "redirects": [
    { "source": "/llms.txt", "destination": "https://<you>.github.io/<repo>/llms.txt", "permanent": true },
    { "source": "/llms-full.txt", "destination": "https://<you>.github.io/<repo>/llms-full.txt", "permanent": true }
  ]
}
```

**Cloudflare Pages**
Add a `_redirects` file:
```
/llms.txt https://<you>.github.io/<repo>/llms.txt 301
/llms-full.txt https://<you>.github.io/<repo>/llms-full.txt 301
```

**Nginx**
Add to your server block:
```nginx
location = /llms.txt { return 301 https://<you>.github.io/<repo>/llms.txt; }
location = /llms-full.txt { return 301 https://<you>.github.io/<repo>/llms-full.txt; }
```

**Static hosts without redirect support**
If your host doesn't support server-side redirects, you can host the `llms.txt` file directly in your site's root directory. The trade-off is you'll need to update it manually or set up a separate sync mechanism.

## Why Static Files Instead of an MCP Server

Most LLMs today discover content by reading pages and fetching URLs. They don't auto-connect to MCP servers or call APIs unprompted. A static JSON API behind `llms.txt` works with every LLM right now, costs $0 to host on GitHub Pages, and requires zero maintenance after setup. When the ecosystem evolves, this approach can be extended.

## Cost

$0. GitHub Actions free tier covers the daily cron. GitHub Pages is free for public repos.

## License

MIT
