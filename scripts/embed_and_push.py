# scripts/embed_and_push.py

import os
import json
import pinecone
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
from dotenv import load_dotenv
import time
from sentence_transformers import SentenceTransformer
load_dotenv()
import re
import unicodedata

def sanitize_id(title, chunk_index):
    # Remove accents and non-ASCII chars
    ascii_title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    # Replace spaces with underscores, remove special characters
    ascii_title = re.sub(r'[^a-zA-Z0-9_-]', '_', ascii_title)
    return f"{ascii_title}_{chunk_index}"


# ENV variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

if PINECONE_INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    print(f"[+] Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384,  # all-MiniLM-L6-v2 outputs 384-dim vectors
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT),
    )
else:
    print(f"[✓] Pinecone index '{PINECONE_INDEX_NAME}' already exists.")

index = pc.Index(PINECONE_INDEX_NAME)

# Load local embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

CHECKPOINT_PATH = "embedding_checkpoint.json"

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, "r") as f:
            return set(json.load(f))
    return set()

def save_checkpoint(id_set):
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump(list(id_set), f)

def load_chunks(cleaned_dir="../data/cleaned"):
    docs = []
    for fname in os.listdir(cleaned_dir):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(cleaned_dir, fname), "r", encoding="utf-8") as f:
            chunks = json.load(f)
            for chunk in chunks:
                docs.append({
                    "content": chunk["content"],
                    "metadata": {
                        "title": chunk["title"],
                        "source": chunk["source"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                        "text": chunk["content"]  # ✅ This makes it retrievable later
                    }
                })
    return docs

def embed_and_push(docs, batch_size=32):
    checkpoint = load_checkpoint()
    new_ids = set()

    for i in tqdm(range(0, len(docs), batch_size)):
        batch = docs[i:i+batch_size]
        batch_filtered = []
        filtered_metas = []

        for doc in batch:
            doc_id = f"{doc['metadata']['title']}_{doc['metadata']['chunk_index']}"
            if doc_id not in checkpoint:
                batch_filtered.append(doc["content"])
                filtered_metas.append(doc["metadata"])

        if not batch_filtered:
            continue

        embeddings = embedding_model.encode(batch_filtered, show_progress_bar=False)

        to_upsert = [
            (sanitize_id(meta['title'], meta['chunk_index']), emb.tolist(), meta)
            for emb, meta in zip(embeddings, filtered_metas)
        ]

        index.upsert(vectors=to_upsert)
        new_ids.update([item[0] for item in to_upsert])
        save_checkpoint(checkpoint.union(new_ids))
        time.sleep(1)  # light sleep just in case

if __name__ == "__main__":
    print("[+] Loading cleaned chunks...")
    documents = load_chunks()
    print(f"[✓] Loaded {len(documents)} chunks.")

    print("[+] Embedding and pushing to Pinecone...")
    embed_and_push(documents)
    print("[✓] All chunks embedded and uploaded.")
