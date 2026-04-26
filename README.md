# 🛍️ ShopAssist — Interactive Product Discovery Chatbot

> An intelligent conversational assistant that streamlines product discovery by understanding customer needs and delivering tailored recommendations.

---

## 📌 Overview

Online shoppers often know what they want but not which product fits best. ShopAssist solves this by acting as a conversational product advisor, it identifies the product category, asks focused clarifying questions, and delivers a tailored recommendation based on the customer's actual needs.

Built for **Accord Business Group**.

---

## ✨ Features

- 🗣️ **Guided discovery flow** — never recommends immediately, asks one question at a time
- 🔍 **RAG pipeline** — retrieves relevant products from PDF catalogs using semantic search
- 🧠 **Claude LLM** — powered by Anthropic's Claude for natural, context-aware conversation
- 💾 **Persistent chat history** — conversations saved to disk, accessible across sessions
- 🌐 **Bilingual** — English and Arabic, auto-detected with a one-click toggle
- 🐳 **Dockerized** — runs in a single container with one command


## 🏗️ Architecture

```
User Message
     │
     ▼
┌─────────────────────────────────────────────┐
│              Streamlit UI                   │
│   Chat interface · History sidebar · Toggle │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│             Chatbot Engine                  │
│                                             │
│  1. Detect language  (Arabic / English)     │
│  2. Classify category (keyword matching)    │
│  3. Retrieve products (RAG search)          │
│  4. Build prompt  (catalog + history)       │
│  5. Call Claude   (LangChain)               │
│  6. Detect stage  (clarifying / recommend)  │
│  7. Save to history (JSON file)             │
└──────┬──────────────────────┬───────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐      ┌──────────────────────┐
│  ChromaDB   │      │     Claude API       │
│             │      |    (Anthropic)       │
│             │      │                      │
│  PDF chunks │      │  Generates natural   │
│  + vectors  │      │  conversation reply  │
└─────────────┘      └──────────────────────┘
```

---

## 📁 Project Structure

```
shopassist/
│
├── app/
│   ├── config.py          # All settings — reads from .env
│   ├── rag.py             # PDF ingestion, chunking, embeddings, retrieval
│   ├── chatbot.py         # Conversation logic + persistent chat history
│   └── streamlit_app.py   # Web UI
│
├── data/
│   ├── raw/               # Product PDF catalog files (add yours here)
│   ├── vectorstore/       # Auto-generated ChromaDB 
│   └── history.json       # Persistent chat history (auto-generated)
│
├── .env.example           # Environment variable template
├── .gitignore             # Keeps .env and sensitive files off GitHub
├── Dockerfile             # Single container setup
└── requirements.txt       # Python dependencies
```

---

## ▶️ How to Run the Project

Run it with **Docker**.

---


### — Run with Docker

#### Step 1 — Make sure Docker is installed
Download from 👉 [docker.com/get-started](https://www.docker.com/get-started)

#### Step 2 — Clone the Repo
git clone https://github.com/Ghassankorhani/Shopassist.git
cd Shopassist

#### Step 3 — Add your API key
cp .env.example .env

Open .env and add:
ANTHROPIC_API_KEY=sk-ant-your-key-here

#### Step 4 — Add your product PDFs
Copy your catalog PDF files into data/raw/:

data/raw/wall_chargers.pdf
data/raw/power_banks.pdf
data/raw/travel_bags.pdf
data/raw/home_kitchen.pdf

### Step 5 — Build the image
docker build -t shopassist .

> ⏳ First build takes time (downloads packages + embedding model).
> After that, rebuilds are much faster.

### Step 6 — Run the container
```
Windows (PowerShell):
powershelldocker run --rm -p 8501:8501 --env-file .env -v "${PWD}/data:/app/data" shopassist

macOS / Linux:
bashdocker run --rm -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" shopassi

```

### Step 7 — Open in your browser
http://localhost:8501


---

## ⚙️ Configuration


| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)*                | Your Anthropic API key                     |
| `CLAUDE_MODEL`      | `claude-haiku-4-5-20251001` | Claude model to use                        |
| `CHUNK_SIZE`        | `500`                       | Characters per text chunk                  |
| `CHUNK_OVERLAP`     | `80`                        | Overlap between chunks                     |
| `TOP_K`             | `6`                         | Number of chunks retrieved per query       |
| `EMBED_MODEL`       | `all-MiniLM-L6-v2`          | Local embedding model (free)               |
| `MAX_TOKENS`        | `1024`                      | Max tokens in Claude's reply               |
| `TEMPERATURE`       | `0.3`                       | LLM creativity (0 = focused, 1 = creative) |

---

## 🔧 Tech Stack

| Component | Technology | Why |
|---|---|---|
| LLM                                                    | Claude (Anthropic) via LangChain          | Strong bilingual support, reliable instruction-following |
| Embeddings                                             | `all-MiniLM-L6-v2` (SentenceTransformers) | Free, runs locally, no API cost                          |
| Vector Store                                           |  ChromaDB                                 | Lightweight, persisted to disk, no server needed         |
| PDF Ingestion                                          | LangChain PyPDFLoader                     | Clean text extraction with metadata                      |
| UI | Streamlit                                         | Fast to build, easy to demo               |                                                          |
| Containerization                                       | Docker                                    | Single container, runs anywhere                          |

---

## 💡 How the Discovery Flow Works

```
Stage 1 — Category Detection
  User message → auto classifier → detect product family
  ≤ 4 PDFs: keyword matching (fast, no extra computation)
  > 4 PDFs: embedding similarity (automatic, scales to any catalog size)
  If ambiguous → ask one question to clarify

Stage 2 — Clarification (max 3 questions)
  Ask the most important spec for that category
  Wall chargers:  wattage? ports? travel use?
  Power banks:    capacity? portability? wireless?
  Travel bags:    trip type? size? laptop sleeve?
  Home & kitchen: item type? household size? key feature?

Stage 3 — Recommendation
  Enough info gathered → recommend 1–3 products
  Each with a brief reason explaining why it fits
```


## 📝 Notes

- Chat history saved to `data/history.json` — persists across sessions
- The `.env` file is excluded from Git, Please insert your Anthropic API key
- PDFs must be placed in `data/raw/` before running

## 🧠 Auto Classification

The system automatically selects the best classification approach based on your catalog size:

| PDFs in `data/raw/` | Mode | How it works |
|---|---|---|
| 4 or fewer | `keywords` | Fast keyword matching — works perfectly for small catalogs |
| 5 or more | `embeddings` | Semantic similarity — scales automatically, no manual work needed |

To expand the catalog just add a new PDF to `data/raw/` and rebuild.
No code changes needed — the system adapts automatically.

---

## 👤 Developer

**Ghassan Korhani**
[github.com/Ghassankorhani](https://github.com/Ghassankorhani/Shopassist)
