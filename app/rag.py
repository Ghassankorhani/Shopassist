import logging
import os
import uuid
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
import chromadb

from config import cfg

log = logging.getLogger(__name__)

## Maps PDF keywords to category names
CATEGORIES = {
    "wall_chargers": "wall_chargers",
    "power_banks":   "power_banks",
    "travel_bags":   "travel_bags",
    "home_kitchen":  "home_kitchen",
}


class RAGPipeline:

    def __init__(self):
        #Load the embedding model
        cache_dir = os.environ.get("SENTENCE_TRANSFORMERS_HOME", None)
        self.model = SentenceTransformer(
            cfg.embed_model,
            cache_folder=cache_dir
        )
        self.client = None
        self.collection = None
        self.total_chunks = 0

    def load(self):
        #Create vectorstore directory
        vs_path = Path(cfg.vs_dir)
        vs_path.mkdir(parents=True, exist_ok=True)

        # Connect to ChromaDB directly
        self.client = chromadb.PersistentClient(path=str(vs_path))

        existing = [c.name for c in self.client.list_collections()]

        if "products" in existing:
            self.collection = self.client.get_collection("products")
            self.total_chunks = self.collection.count()
            log.info("%d chunks loaded.", self.total_chunks)
            # If chunks are too few something went wrong — rebuild
            if self.total_chunks < 10:
                log.warning("Too few chunks (%d) — rebuilding vectorstore...", self.total_chunks)
                self.client.delete_collection("products")
                self._build()
        else:
            log.info("Building collection from PDFs...")
            self._build()

    def _build(self):
        #Read all PDFs, split into chunks, embed and store in ChromaDB
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=cfg.chunk_size,
            chunk_overlap=cfg.chunk_overlap,
        )

        # Create ChromaDB collection with cosine similarity
        self.collection = self.client.create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"}
        )

        all_texts = []
        all_ids = []
        all_embeddings = []
        all_metadatas = []

        for pdf in Path(cfg.data_dir).glob("*.pdf"):
            ## Detect category from filename (default to "unknown" if no match)
            cat = next(
                (v for k, v in CATEGORIES.items() if k in pdf.stem.lower()),
                "unknown"
            )
            #Tag eacch page with category
            pages = PyPDFLoader(str(pdf)).load()
            for p in pages:
                p.metadata["category"] = cat
            #Split into chunks
            chunks = splitter.split_documents(pages)

            for chunk in chunks:
                text = chunk.page_content.strip()
                if not text:
                    continue
                all_texts.append(text)
                all_ids.append(str(uuid.uuid4()))
                all_metadatas.append({"category": cat, "source": pdf.name})

            log.info("  %s → %d chunks (category: %s)", pdf.name, len(chunks), cat)

        if not all_texts:
            raise ValueError("No text found in PDFs!")

        log.info("Embedding %d chunks...", len(all_texts))

        # Embed in batches of 50 
        batch_size = 50
        for i in range(0, len(all_texts), batch_size):
            batch_texts = all_texts[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]
            batch_metas = all_metadatas[i:i + batch_size]

            vectors = self.model.encode(
                batch_texts,
                normalize_embeddings=True
            ).tolist()

            self.collection.add(
                documents=batch_texts,
                embeddings=vectors,
                ids=batch_ids,
                metadatas=batch_metas
            )
            log.info("  Embedded batch %d/%d", min(i + batch_size, len(all_texts)), len(all_texts))

        self.total_chunks = len(all_texts)
        log.info("Vectorstore ready — %d total chunks.", self.total_chunks)

    def retrieve(self, query: str, cat: str | None = None) -> List[Document]:
        #Conert the query into vectors and search ChromaDB for the most relevant product chunks
        query_vector = self.model.encode(
            [query],
            normalize_embeddings=True
        ).tolist()[0]

        where = {"category": cat} if cat and cat != "unknown" else None

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=cfg.top_k,
            where=where,
        )

        docs = []
        for i, text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            docs.append(Document(page_content=text, metadata=meta))

        return docs