# app/chat_app.py

import os
import streamlit as st
from dotenv import load_dotenv
import pinecone
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from groq import Groq
from email_utils import send_query_email
import streamlit as st

# === Load ENV Vars ===
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_ENVIRONMENT = st.secrets["PINECONE_ENVIRONMENT"]
PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# === Initialize Clients ===
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
index = pc.Index(PINECONE_INDEX_NAME)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
groq_client = Groq(api_key=GROQ_API_KEY)

# === Streamlit UI ===
st.title("🧠 Ask Nietzsche (RAG vs. Raw LLM)")
st.markdown("Ask anything about Nietzsche’s works, life, or interpretations.")

query = st.text_input("Your question:", placeholder="What did Nietzsche mean by eternal recurrence?")
use_rag = st.checkbox("Use RAG (Retrieval-Augmented Generation)", value=True)

if query:
    if use_rag:
        # Embed query
        query_embedding = embedder.encode([query])[0]

        # Search Pinecone
        results = index.query(vector=query_embedding.tolist(), top_k=5, include_metadata=True)
        docs = [match['metadata'] for match in results['matches']]
        contexts = []
        for match in results['matches']:
            title = match['metadata'].get('title', 'Unknown Title')
            chunk_index = match['metadata'].get('chunk_index', 'N/A')
            chunk_text = match.get('content', '') or match['metadata'].get('text', 'No content available')
            contexts.append(f"{title} [chunk {chunk_index}]:\n{chunk_text}")

        context_str = "\n\n---\n\n".join(contexts)

        prompt = f"""
        You are a Nietzsche expert AI. Use the context below to answer the user's question truthfully and concisely.
        If unsure, say "I don’t know."

        Context:
        {context_str}

        User Question:
        {query}
        """
    else:
        prompt = f"""
        You are a Nietzsche expert AI. Answer the user's question truthfully and in Nietzschean style.
        If unsure, say "I don’t know."

        User Question:
        {query}
        """

    # Call Groq LLM
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",  # or "mixtral-8x7b-32768"
        messages=[{"role": "user", "content": prompt}]
    )
    send_query_email(query, use_rag, response)

    st.markdown("### 🤖 Answer:")
    st.markdown(response.choices[0].message.content)
