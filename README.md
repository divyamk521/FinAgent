# 📈 FinAgent

An AI-powered financial analyst built with **LangGraph**, **Groq LLM** (free), and a modular tool layer backed by **yfinance** and **Finlight** — all free to use.

---

## 🗂️ Project Structure

```
finagent/
├── agent/
│   ├── __init__.py        # Exports create_graph
│   ├── graph.py           # LangGraph graph + Groq LLM
│   ├── state.py           # AgentState TypedDict
│   └── tools.py           # All financial tools
├── api/
│   ├── __init__.py
│   └── server.py          # FastAPI REST server
├── ui/
│   ├── index.html         # Standalone web chat UI
│   └── streamlit_app.py   # Streamlit chat UI
├── .env.example
├── .gitignore
├── config.py
├── main.py                # CLI entrypoint
├── README.md
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Unzip and enter the folder
```bash
cd finagent
```

### 2. Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get your free API keys

| Key | Where |
|---|---|
| `GROQ_API_KEY` | https://console.groq.com — sign up, create key (no credit card) |
| `FINLIGHT_API_KEY` | https://app.finlight.me — register for free tier |
| `JINA_API_KEY` _(optional)_ | https://jina.ai/reader — richer analyst forecasts |

### 5. Configure `.env`
```bash
cp .env.example .env
# Open .env and fill in your keys
```

---

## ▶️ Running the App

### Option A — Streamlit UI (simplest)
```bash
streamlit run ui/streamlit_app.py
```
Open http://localhost:8501

### Option B — Web UI + FastAPI (full stack)
```bash
# Terminal 1 — start the API server
uvicorn api.server:app --reload --port 8000

# Terminal 2 — open the HTML UI
# Just open ui/index.html in your browser
```
Open `ui/index.html` in your browser, set API URL to `http://localhost:8000`.

### Option C — CLI
```bash
python main.py                            # interactive
python main.py "How is Tesla doing?"      # single query
```

---




---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check server + model |
| POST | `/chat` | Send a message |

### POST /chat
```json
{
  "message": "How is Apple stock doing?",
  "history": []
}
```
Response:
```json
{
  "response": "...",
  "model": "llama-3.3-70b-versatile"
}
```

---

## ➕ Extending

- **Add a tool:** Add `@tool` function to `agent/tools.py`, append to `ALL_TOOLS`.
- **Swap the LLM:** Edit `agent/graph.py` — replace `ChatGroq` with any LangChain chat model.
- **Add memory:** Use LangGraph's checkpointer in `agent/graph.py`.

Author:Divya M K