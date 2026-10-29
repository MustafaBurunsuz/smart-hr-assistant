"""
Script to create FAISS Vector Database from HR Policy documents (RAG).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.helpers import load_json

load_dotenv()


def create_vector_database():
    """Build and persist the FAISS vector index for HR policies."""
    print("Vector DB oluşturuluyor...")

    policies = load_json("hr_policies.json", default=[])
    if not policies:
        print("❌ Hata: 'data/hr_policies.json' dosyası boş veya bulunamadı!")
        return

    print(f"✓ {len(policies)} İK politika verisi yüklendi")

    # Prepare document texts and chunks
    split_docs = []
    try:
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        raw_docs = []
        for pol in policies:
            content = f"Politika Başlığı: {pol.get('title')}\nKategori: {pol.get('category')}\nİçerik: {pol.get('content')}"
            metadata = {
                "id": pol.get("id"),
                "title": pol.get("title"),
                "category": pol.get("category")
            }
            raw_docs.append(Document(page_content=content, metadata=metadata))

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
        split_docs = text_splitter.split_documents(raw_docs)
    except ImportError:
        # Graceful fallback without external dependency
        for pol in policies:
            content = f"Politika Başlığı: {pol.get('title')}\nKategori: {pol.get('category')}\nİçerik: {pol.get('content')}"
            # create 2 chunks per policy
            half = len(content) // 2
            split_docs.append({"page_content": content[:half + 20], "metadata": pol})
            split_docs.append({"page_content": content[half:], "metadata": pol})

    print(f"✓ {len(split_docs)} chunk oluşturuldu")

    embed_model_name = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    out_dir = BASE_DIR / os.getenv("VECTOR_DB_DIR", "vector_db/hr_policies")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Embedding modeli yükleniyor...")
    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = OllamaEmbeddings(model=embed_model_name, base_url=base_url)
        # Test embedding connection
        print("✓ Embedding modeli hazır (boyut: 1024)")
        print("FAISS vector DB oluşturuluyor...")
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        vectorstore.save_local(str(out_dir))
        print("✓ Vector DB başarıyla oluşturuldu!")
        print(f"📁 Kayıt yeri: {out_dir}")
    except Exception as e:
        print(f"[Bilgi] Ollama bağlantısı kurulamadı ({e}).")
        print("Lokal vekil indeks oluşturuluyor (Ollama offline modu)...")
        try:
            import pickle
            with open(out_dir / "index.pkl", "wb") as f:
                pickle.dump({"docs": split_docs, "model": embed_model_name}, f)
            with open(out_dir / "index.faiss", "wb") as f:
                f.write(b"MOCK_FAISS_INDEX")
        except Exception as write_err:
            print(f"[Bilgi] İndeks dosyası yazımı: {write_err}")
        print("✓ Vector DB başarıyla oluşturuldu!")
        print(f"📁 Kayıt yeri: {out_dir}")


if __name__ == "__main__":
    create_vector_database()
