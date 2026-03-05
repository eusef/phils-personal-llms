# Phil Johnston, II - Personal API

Turns my personal website ([philjohnstonii.com](https://philjohnstonii.com)) into a structured API that LLMs and agents can discover and query.

## How It Works

1. A GitHub Action scrapes my Squarespace site daily and commits structured JSON to `data/`
2. GitHub Pages serves those JSON files as a public API at `eusef.github.io/phils-personal-llms/api/`
3. An `llms.txt` file on my website points agents to the API and includes my full profile inline

## API Endpoints

No authentication required. Updated daily at 6 AM UTC.

| Endpoint | Description |
|---|---|
| [`/api/profile.json`](https://eusef.github.io/phils-personal-llms/api/profile.json) | Bio, roles, location, contact |
| [`/api/resume.json`](https://eusef.github.io/phils-personal-llms/api/resume.json) | Career timeline, skills, differentiators |
| [`/api/blog.json`](https://eusef.github.io/phils-personal-llms/api/blog.json) | All blog posts with excerpts |
| [`/llms.txt`](https://eusef.github.io/phils-personal-llms/llms.txt) | Standard llms.txt with full inline content |
| [`/llms-full.txt`](https://eusef.github.io/phils-personal-llms/llms-full.txt) | Complete profile for direct LLM consumption |

## Discovery Flow

```
Agent visits philjohnstonii.com/llms.txt
  -> Gets full profile inline (enough for most queries)
  -> Follows API links for structured JSON data
```

## Project Structure

```
phils-personal-llms/
├── data/                        # Scraped JSON (auto-updated by GitHub Action)
│   ├── profile.json
│   ├── resume.json
│   └── blog.json
├── scraper/
│   ├── scrape.py                # Python scraper for Squarespace site
│   └── requirements.txt
├── docs/
│   └── index.html               # GitHub Pages landing page
├── .github/workflows/
│   └── scrape.yml               # Daily scrape + Pages deployment
├── llms.txt                     # For Squarespace + GitHub Pages
└── llms-full.txt                # Full content dump
```

## Setup

To deploy your own version:

1. Fork this repo
2. Update `scraper/scrape.py` with your own site URL and page structure
3. Enable GitHub Pages (Settings > Pages > Source: GitHub Actions)
4. Run the workflow manually (Actions > "Scrape Website & Deploy" > Run workflow)
5. Upload `llms.txt` to your website root
6. Verify at `https://<your-username>.github.io/<repo-name>/api/profile.json`

## License

MIT
