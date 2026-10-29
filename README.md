# Code-Niti Mini

A small, teachable RAG app that indexes supported text and code files from a **public GitHub repository** and answers questions with source snippets.

## Project structure

```text
code-niti-mini/
├── app.py                    # Streamlit interface
├── code_niti/
│   ├── __init__.py
│   ├── github_loader.py       # Fetches and filters public repository files
│   └── rag.py                 # Chunks, embeds, retrieves, and asks the LLM
├── .env.example               # Safe configuration template (no secret)
├── .gitignore
└── requirements.txt
```

## Run on Windows in VS Code

1. Python 3.14.3 (64-bit) works for this project; install Git if it is not already installed, then open this folder in VS Code.
2. In the VS Code terminal, create and activate a virtual environment:

   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey) and put it in `GOOGLE_API_KEY` (never commit `.env`). Google is tried first. To enable fallback, add a Groq key as `GROQ_API_KEY`. If Google's request fails, the app automatically tries Groq. Configure each provider's endpoint and model separately in `.env`.
4. Start the app:

   ```powershell
   streamlit run app.py
   ```

5. Open the local address printed in the terminal, enter a public GitHub URL, index it, and ask a question. The first index downloads the Sentence Transformers model once.

## Staged learning path

1. **UI:** run Streamlit and see the repository input.
2. **Loading:** index a small public repository; inspect supported file counts.
3. **Embeddings and FAISS:** local model turns chunks into vectors and FAISS finds similar chunks.
4. **Generation and fallback:** Gemini answers from retrieved snippets first; if its request fails and a Groq key is configured, Groq is tried next. The UI identifies which provider answered and shows the retrieved sources.

## Sharing it

For a public hosted app, deploy the code to a hosting service and configure `GOOGLE_API_KEY` and optionally `GROQ_API_KEY` as private secrets. Visitors then use the app without entering their own keys. Calls consume the operator's provider quota and are subject to each provider's current limits and pricing; check the current terms before sharing widely. See Google's [OpenAI compatibility guide](https://ai.google.dev/gemini-api/docs/openai) and Groq's [OpenAI compatibility guide](https://console.groq.com/docs/openai).

No provider key means the app can still index and retrieve locally, but hosted LLM answers will not run. A fully local model (for example through Ollama) can avoid a paid API, but a public website cannot use a visitor's computer to run the model; the server operator must run and pay the hardware cost. We can add local Ollama support as a later lesson.

## MVP boundaries

Public repositories only; supported text/code formats only; a 30 MB archive, 500-file, and 200 KB per-file cap; no persistent index between app sessions yet. Do not use this demo to ingest private or sensitive code.
