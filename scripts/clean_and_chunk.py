# scripts/clean_and_chunk.py

import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

RAW_DIRS = ["../data/raw/wiki", "../data/raw/gutenberg"]
OUT_DIR = "../data/cleaned"
CHUNK_SIZE = 1000  # adjust as needed
CHUNK_OVERLAP = 200

def clean_text_gutenberg(text):
    """Remove Gutenberg header/footer and any weird formatting."""
    start = text.find("*** START OF")
    end = text.find("*** END OF")
    if start != -1 and end != -1:
        text = text[start:end]
    return text.replace("\r", "").strip()

def clean_text_wiki(text):
    """Simple Wikipedia cleaner—could be expanded later."""
    return text.replace("\n\n", "\n").strip()

def process_file(path, source):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    title = data["title"]
    text = data["text"]

    if source == "gutenberg":
        text = clean_text_gutenberg(text)
    elif source == "wiki":
        text = clean_text_wiki(text)

    return title, text

def chunk_text(text, title, source):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_text(text)
    return [
        {
            "title": title,
            "source": source,
            "content": chunk,
            "metadata": {
                "chunk_index": idx
            }
        }
        for idx, chunk in enumerate(chunks)
    ]

def save_chunks(chunks, out_dir, source, title):
    safe_title = title.replace(" ", "_")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{source}__{safe_title}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for raw_dir in RAW_DIRS:
        source = "wiki" if "wiki" in raw_dir else "gutenberg"
        for fname in os.listdir(raw_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(raw_dir, fname)
            title, text = process_file(fpath, source)
            chunks = chunk_text(text, title, source)
            save_chunks(chunks, OUT_DIR, source, title)
            print(f"[✓] Processed {title} ({len(chunks)} chunks)")

if __name__ == "__main__":
    main()
