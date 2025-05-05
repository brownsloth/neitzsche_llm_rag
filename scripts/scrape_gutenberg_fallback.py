# scripts/scrape_gutenberg_fallback.py

import requests
import os
import json

BOOKS = {
    "The Antichrist (Eng)": "https://www.gutenberg.org/cache/epub/19322/pg19322.txt",
    "Beyond Good and Evil (Eng)": "https://www.gutenberg.org/cache/epub/4363/pg4363.txt",
    "The Dawn of Day (Eng)": "https://www.gutenberg.org/cache/epub/37407/pg37407.txt"
}

def download_txt(title, url, out_dir="../data/raw/gutenberg"):
    os.makedirs(out_dir, exist_ok=True)
    print(f"[+] Downloading: {title} ({url})")

    response = requests.get(url)
    if response.status_code != 200:
        print(f"[!] Failed to download {title} — Status Code: {response.status_code}")
        return

    text = response.text
    filename = f"{title.replace(' ', '_').replace('(', '').replace(')', '')}.json"
    path = os.path.join(out_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "title": title,
            "text": text
        }, f, indent=2)

if __name__ == "__main__":
    for title, url in BOOKS.items():
        download_txt(title, url)
