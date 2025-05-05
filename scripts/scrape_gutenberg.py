# scripts/scrape_gutenberg.py

import requests
import os
import json
from tqdm import tqdm

BASE_URL = "https://www.gutenberg.org/files/{id}/{id}-0.txt"
BOOKS = {
    # "Thus Spake Zarathustra (Eng)": 7205,
    "Beyond Good and Evil (Eng)": 4363,
    "The Antichrist (Eng)": 19322,
    "The Dawn of Day (Eng)": 37407,
    # "Human, All Too Human (Eng)": 52263
}

def download_and_save(title, gid, out_dir="../data/raw/gutenberg"):
    os.makedirs(out_dir, exist_ok=True)
    url = BASE_URL.format(id=gid)
    print(f"[+] Downloading: {title} ({url})")

    response = requests.get(url)
    if response.status_code != 200:
        print(f"[!] Failed to download {title}")
        return

    content = response.text
    filename = f"{title.replace(' ', '_')}.json"
    path = os.path.join(out_dir, filename)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "title": title,
            "text": content
        }, f, indent=2)

if __name__ == "__main__":
    for title, gid in tqdm(BOOKS.items()):
        download_and_save(title, gid)
