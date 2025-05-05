# scripts/scrape_wikipedia.py

import wikipediaapi
import os
import json

wiki = wikipediaapi.Wikipedia(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36', language='en')

def get_page_and_links(title):
    page = wiki.page(title)
    if not page.exists():
        print(f"[!] Page '{title}' not found.")
        return None, []
    links = [link.title for link in page.links.values()]
    return page.text, links

def save_article(title, text, out_dir="../data/raw/wiki"):
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{title.replace(' ', '_')}.json"
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
        json.dump({"title": title, "text": text}, f, indent=2)

def scrape_related_articles(seed_title="Friedrich Nietzsche", depth=1):
    seen = set()
    queue = [seed_title]
    
    for _ in range(depth):
        next_queue = []
        for title in queue:
            if title in seen:
                continue
            print(f"[+] Scraping '{title}'")
            text, links = get_page_and_links(title)
            if text:
                save_article(title, text)
                seen.add(title)
                next_queue.extend(links[:20])  # throttle link expansion
        queue = next_queue

if __name__ == "__main__":
    scrape_related_articles("Friedrich Nietzsche", depth=3)
