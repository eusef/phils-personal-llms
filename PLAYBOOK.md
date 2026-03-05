# Playbook: Turn Any Personal Website Into an LLM-Discoverable API

A repeatable workflow for making your personal website machine-readable. No servers to run, no accounts beyond GitHub, no manual updates after initial setup.

## What You End Up With

- `yoursite.com/llms.txt` - agents check this standard path and get your full profile
- `yourusername.github.io/repo/api/*.json` - structured JSON endpoints anyone can fetch
- A daily GitHub Action that scrapes your site and keeps everything in sync

## Architecture

```
yoursite.com/llms.txt (redirect)
  -> github.io/repo/llms.txt (auto-updated daily)
     -> github.io/repo/api/profile.json
     -> github.io/repo/api/resume.json
     -> github.io/repo/api/blog.json
```

No servers. No databases. Just static files served by GitHub Pages, refreshed by a cron job.

## Step-by-Step

### 1. Create the GitHub Repo

```
your-repo/
├── data/              # JSON output (written by scraper)
├── scraper/
│   ├── scrape.py      # Python scraper customized for your site
│   └── requirements.txt
├── docs/
│   └── index.html     # Landing page for GitHub Pages
├── .github/workflows/
│   └── scrape.yml     # Daily scrape + deploy
├── llms.txt           # Full inline content + API links
└── llms-full.txt      # Extended version
```

### 2. Write the Scraper

Customize `scraper/scrape.py` for your site's structure. The pattern:

- Use `requests` + `beautifulsoup4`
- Scrape each major page (home, about, blog, etc.)
- Output structured JSON to `data/`
- Include `scraped_at` timestamps in each file

Key decisions:
- Identify your pages by their URL paths (e.g., `/about-me`, `/blog`)
- Find content by heading text, not CSS classes (headings change less often)
- Include a hardcoded list of known blog post URLs as fallback
- Keep the JSON schema simple and flat

`requirements.txt`:
```
requests>=2.31.0
beautifulsoup4>=4.12.0
```

### 3. Define Your JSON Schema

Design the output files around how an agent would ask about you:

**profile.json** - "Who is this person?"
```json
{
  "name": "...",
  "tagline": "...",
  "roles": ["...", "..."],
  "location": "...",
  "website_url": "...",
  "contact_form_url": "..."
}
```

**resume.json** - "What's their background?"
```json
{
  "summary": "...",
  "career_timeline": [{"year": "...", "role": "...", "company": "..."}],
  "technical_focus": ["..."],
  "differentiators": [{"title": "...", "description": "..."}]
}
```

**blog.json** - "What do they write about?"
```json
{
  "posts": [{
    "title": "...",
    "date": "...",
    "url": "...",
    "slug": "...",
    "excerpt": "...",
    "full_content": "...",
    "tags": ["..."]
  }]
}
```

### 4. Set Up the GitHub Action

The workflow does two jobs:
1. **Scrape** - runs the Python scraper, commits changes to `data/` if anything changed
2. **Deploy** - copies data files + llms.txt into a `_site/` directory and deploys to GitHub Pages

Triggers:
- `schedule: cron '0 6 * * *'` - daily at 6 AM UTC
- `workflow_dispatch` - manual trigger
- `push: branches: [main]` - on every push

The scrape job only commits if data actually changed (no empty commits).

### 5. Write llms.txt

This is the discovery layer. Follow the community standard format:

```markdown
# Your Name

> One-paragraph summary with key facts an agent needs.

## Profile
[Full inline content - don't make agents follow links for basic info]

## Career
[Timeline with dates, roles, companies]

## Blog
[Post titles with dates and URLs]

## Structured Data API
[Links to your JSON endpoints]
```

Put everything inline. An agent should be able to answer "who is this person?" from llms.txt alone without fetching anything else.

Also create `llms-full.txt` with even more detail (full blog excerpts, complete differentiators, etc.).

### 6. Enable GitHub Pages

In your repo: **Settings > Pages > Source: GitHub Actions**

Then trigger the workflow manually: **Actions > "Scrape Website & Deploy" > Run workflow**

Verify at `https://yourusername.github.io/your-repo/api/profile.json`

### 7. Connect Your Website

On your website's hosting platform, set up redirects from the standard llms.txt paths to your GitHub Pages URLs:

```
/llms.txt      -> https://yourusername.github.io/your-repo/llms.txt
/llms-full.txt -> https://yourusername.github.io/your-repo/llms-full.txt
```

For **Squarespace** specifically:
- Settings > Advanced > URL Mappings
- Add: `/llms.txt -> https://yourusername.github.io/your-repo/llms.txt 301`
- Add: `/llms-full.txt -> https://yourusername.github.io/your-repo/llms-full.txt 301`

For **other platforms**: most support 301 redirects or rewrite rules in their config.

## What Worked / Lessons Learned

1. **llms.txt with full inline content is the most important piece.** Most LLMs today read pages and fetch URLs. They don't connect to MCP servers or call APIs unprompted. Put your content where they'll find it.

2. **Static JSON over HTTP beats any "smart" server.** GitHub Pages is free, fast, globally cached, and always on. No cold starts, no auth, no rate limits to worry about.

3. **Server-side redirects (301) are critical.** JavaScript redirects don't work for LLM crawlers since they don't execute JS. Use your hosting platform's URL mapping or redirect rules.

4. **Design JSON around questions, not pages.** Structure your data the way an agent would ask: "who is this person?" (profile), "what's their experience?" (resume), "what do they write about?" (blog).

5. **The daily scrape is the glue.** You never manually update the API. Edit your website, the scraper picks it up within 24 hours. The `workflow_dispatch` trigger lets you force an immediate refresh.

6. **MCP servers are premature for discovery.** No major LLM auto-discovers and connects to MCP servers from llms.txt today. The static API + llms.txt approach works now and can be extended later when the ecosystem catches up.

## Cost

$0. GitHub Actions free tier covers the daily cron. GitHub Pages is free for public repos.
