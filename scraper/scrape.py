#!/usr/bin/env python3
"""
Sitemap-driven website scraper.

Reads config.json, traverses the sitemap, scrapes each page generically,
and generates llms.txt and llms-full.txt for LLM consumption.
"""

import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)

SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".zip", ".gz", ".css", ".js", ".xml", ".json",
}

SKIP_PATHS = {"/feed", "/rss", "/atom", "/admin", "/wp-admin", "/wp-login.php"}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_timestamp():
    return datetime.utcnow().isoformat() + "Z"


def fetch(url, timeout=15):
    try:
        headers = {"User-Agent": "auto-llms-txt/1.0 (sitemap scraper; github.com/eusef/auto-llms-txt)"}
        r = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        print(f"  WARN: {url} -> {e}")
        return None


def find_sitemap_url(base_url):
    """Find sitemap URL from robots.txt or common locations."""
    # Check robots.txt
    r = fetch(urljoin(base_url, "/robots.txt"))
    if r:
        for line in r.text.splitlines():
            if line.lower().startswith("sitemap:"):
                url = line.split(":", 1)[1].strip()
                print(f"  Found sitemap in robots.txt: {url}")
                return url

    # Try common locations
    for path in ["/sitemap.xml", "/sitemap_index.xml"]:
        url = urljoin(base_url, path)
        r = fetch(url)
        if r and r.status_code == 200 and "xml" in r.headers.get("content-type", "").lower():
            print(f"  Found sitemap at: {url}")
            return url

    return None


def parse_sitemap(sitemap_url, depth=0):
    """Parse a sitemap or sitemap index and return all page URLs."""
    if depth > 3:
        return []

    r = fetch(sitemap_url)
    if not r:
        return []

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print(f"  WARN: XML parse error for {sitemap_url}: {e}")
        return []

    # Strip namespace for easier tag matching
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Sitemap index: recurse into sub-sitemaps
    if "sitemapindex" in root.tag.lower():
        urls = []
        for loc in root.findall(f".//{ns}loc"):
            urls.extend(parse_sitemap(loc.text.strip(), depth + 1))
        return urls

    # Regular sitemap: collect <loc> entries
    return [loc.text.strip() for loc in root.findall(f".//{ns}loc")]


def should_skip(url, base_url, exclude_patterns):
    """Return True if this URL should not be scraped."""
    parsed = urlparse(url)
    base_parsed = urlparse(base_url)

    # Must be same domain
    if parsed.netloc != base_parsed.netloc:
        return True

    path = parsed.path.lower()

    # Skip non-HTML file extensions
    if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
        return True

    # Skip known non-content paths
    if any(path == p or path.startswith(p + "/") for p in SKIP_PATHS):
        return True

    # Skip URLs with query strings (often dynamic/duplicate)
    if parsed.query:
        return True

    # Skip fragment-only URLs
    if parsed.fragment and not parsed.path:
        return True

    # Skip configured patterns.
    # Path patterns (starting with "/"):
    #   "/blog"  → exact match only — excludes /blog but not /blog/post-slug
    #   "/cdn-cgi/" → prefix match — excludes /cdn-cgi/anything
    # Other patterns (e.g. "?format=json"): substring match against the full URL.
    for pattern in exclude_patterns:
        if pattern.startswith("/"):
            if pattern.endswith("/"):
                if path.startswith(pattern) or path == pattern.rstrip("/"):
                    return True
            else:
                if path == pattern:
                    return True
        elif pattern in url:
            return True

    return False


def scrape_page(url):
    """
    Generic page scraper. Extracts title, meta description, and main body text.
    Works across CMS platforms (Squarespace, WordPress, Webflow, etc.).
    """
    r = fetch(url)
    if not r:
        return None

    soup = BeautifulSoup(r.content, "html.parser")

    # Remove elements that aren't content
    for tag in soup.find_all(["nav", "footer", "header", "script", "style", "aside", "form"]):
        tag.decompose()

    page = {
        "url": url,
        "title": None,
        "description": None,
        "content": "",
    }

    # Title: prefer h1 over <title> tag (title tag often has site name appended)
    h1 = soup.find("h1")
    title_tag = soup.find("title")
    if h1 and h1.get_text(strip=True):
        page["title"] = h1.get_text(strip=True)
    elif title_tag:
        page["title"] = title_tag.get_text(strip=True)

    # Meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        page["description"] = meta["content"].strip()

    # Main content: prefer <main> or <article>
    content_root = soup.find("main") or soup.find("article") or soup.find("body") or soup

    blocks = []
    seen = set()
    for tag in content_root.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        # Skip short fragments and duplicates
        if not text or len(text) < 15 or text in seen:
            continue
        seen.add(text)
        blocks.append(text)

    page["content"] = "\n".join(blocks)

    return page


def generate_llms_txt(pages, config):
    """Generate llms.txt (concise index) and llms-full.txt (full content)."""
    site_name = config.get("site_name", "Website")
    description = config.get("description", "")
    base_url = config.get("website_url", "")
    today = get_timestamp()[:10]

    # ── llms.txt (concise) ────────────────────────────────────────────────────

    lines = [f"# {site_name}", ""]

    if description:
        lines += [f"> {description}", ""]

    lines += ["## Pages", ""]
    for page in pages:
        title = page.get("title") or page["url"]
        url = page["url"]
        desc = page.get("description") or ""
        entry = f"- [{title}]({url})"
        if desc:
            entry += f": {desc}"
        lines.append(entry)

    lines += [
        "",
        "## About",
        "",
        f"Source: {base_url}",
        f"Last updated: {today}",
        "",
    ]

    # ── llms-full.txt (verbose) ───────────────────────────────────────────────

    full = [f"# {site_name} — Full Content", ""]

    if description:
        full += [f"> {description}", ""]

    full += ["---", ""]

    for page in pages:
        title = page.get("title") or page["url"]
        url = page["url"]
        desc = page.get("description") or ""
        content = page.get("content") or ""

        full += [f"## {title}", "", f"URL: {url}"]
        if desc:
            full.append(f"Summary: {desc}")
        full.append("")
        if content:
            full.append(content)
        full += ["", "---", ""]

    full += [f"Source: {base_url}", f"Last updated: {today}", ""]

    return "\n".join(lines), "\n".join(full)


def save_text(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Saved: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    config = load_config()
    base_url = config["website_url"].rstrip("/")
    exclude_patterns = config.get("exclude_patterns", [])

    print(f"Scraping: {base_url}")
    print(f"Timestamp: {get_timestamp()}")
    print()

    # Discover URLs via sitemap
    print("Finding sitemap...")
    sitemap_url = find_sitemap_url(base_url)
    if sitemap_url:
        all_urls = parse_sitemap(sitemap_url)
        print(f"Sitemap contains {len(all_urls)} URLs")
    else:
        print("No sitemap found, will scrape homepage only")
        all_urls = [base_url]

    # Filter
    urls = [u for u in all_urls if not should_skip(u, base_url, exclude_patterns)]

    # Deduplicate, preserve order
    seen_urls = set()
    unique_urls = []
    for u in urls:
        if u not in seen_urls:
            seen_urls.add(u)
            unique_urls.append(u)

    print(f"Pages to scrape: {len(unique_urls)}")
    print()

    # Scrape each page
    pages = []
    for i, url in enumerate(unique_urls, 1):
        print(f"[{i}/{len(unique_urls)}] {url}")
        page = scrape_page(url)
        if page and (page.get("title") or page.get("content")):
            pages.append(page)
        time.sleep(0.5)  # be polite

    print(f"\nScraped {len(pages)} pages with content")

    # Generate output
    print("\nGenerating llms.txt and llms-full.txt...")
    concise, full = generate_llms_txt(pages, config)
    save_text("llms.txt", concise)
    save_text("llms-full.txt", full)

    print(f"\nDone! {len(pages)} pages indexed.")


if __name__ == "__main__":
    main()
