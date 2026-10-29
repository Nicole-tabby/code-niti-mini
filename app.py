"""Code-Niti Mini: ask questions about a public GitHub repository."""

import os

import streamlit as st
from dotenv import load_dotenv

from code_niti.github_loader import load_repository
from code_niti.rag import answer_question, build_index

load_dotenv()
st.set_page_config(page_title="Code-Niti Mini", page_icon="🧭", layout="wide")
st.title("🧭 Code-Niti Mini")
st.caption("A small RAG assistant for exploring public GitHub repositories.")


def setting(name: str, default: str = "") -> str:
    """Read a value from local .env first, then hosted Streamlit secrets."""
    value = os.getenv(name, "")
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, AttributeError):
        return default

with st.sidebar:
    st.header("1. Choose a repository")
    repo_url = st.text_input("Public GitHub URL", placeholder="https://github.com/owner/repo")
    index_button = st.button("Index repository", type="primary", use_container_width=True)
    st.divider()
    st.header("2. Ask a question")
    st.caption("The first run downloads the embedding model. Indexing may take a little while.")

if index_button:
    try:
        with st.spinner("Reading supported files from GitHub…"):
            documents, revision = load_repository(repo_url)
        if not documents:
            st.warning("No supported text or code files were found in this repository.")
        else:
            with st.spinner(f"Creating embeddings for {len(documents)} files…"):
                st.session_state.retriever = build_index(documents)
            st.session_state.repo_url = repo_url
            st.session_state.revision = revision
            st.session_state.indexed_file_count = len(documents)
            st.session_state.index_notice = True
    except Exception as exc:  # Show actionable errors in the UI.
        st.error(str(exc))

if "retriever" in st.session_state:
    st.info(f"Repository: {st.session_state.repo_url} · revision {st.session_state.revision[:12]}")
    if st.session_state.get("index_notice"):
        st.success(f"Repository successfully indexed ({st.session_state.indexed_file_count} files). Please proceed to ask a question.")

    st.markdown("**Not sure what to ask? Try one of these:**")
    suggestions = [
        "What does this project do?",
        "Where is the main entry point?",
        "What are the main dependencies?",
        "Where are tests located?",
    ]
    suggestion_columns = st.columns(2)
    for position, suggestion in enumerate(suggestions):
        if suggestion_columns[position % 2].button(suggestion, key=f"suggestion_{position}", use_container_width=True):
            st.session_state.question_input = suggestion

    question = st.text_input("Your question", placeholder="Where is authentication handled?", key="question_input")
    if st.button("Get answer") and question.strip():
        providers = []
        google_key = setting("GOOGLE_API_KEY") or setting("LLM_API_KEY")
        groq_key = setting("GROQ_API_KEY")
        if google_key:
            providers.append({
                "name": "Google Gemini",
                "api_key": google_key,
                "base_url": setting("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                "model": setting("GOOGLE_MODEL", "gemini-3.8-flash"),
            })
        if groq_key:
            providers.append({
                "name": "Groq",
                "api_key": groq_key,
                "base_url": setting("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
                "model": setting("GROQ_MODEL", "openai/gpt-oss-20b"),
            })
        if not providers:
            st.warning("Retrieval is ready, but no LLM key is configured. Add GOOGLE_API_KEY, GROQ_API_KEY, or both to your local .env or deployment secrets to generate answers.")
        else:
            with st.spinner("Searching the repository and writing an answer…"):
                try:
                    answer, sources, provider_name, fallback_message = answer_question(
                        question, st.session_state.retriever, providers
                    )
                    if fallback_message:
                        st.info(f"Google Gemini was unavailable, so this answer came from {provider_name}.")
                    else:
                        st.caption(f"Answered with {provider_name}.")
                    st.markdown(answer)
                    with st.expander("Sources used"):
                        for source in sources:
                            st.markdown(f"**`{source['path']}` · chunk {source['chunk']}**\n\n```text\n{source['text']}\n```")
                except Exception as exc:
                    st.error(f"Could not generate an answer: {exc}")
else:
    st.markdown("Enter a public GitHub repository URL in the sidebar, then select **Index repository**.")
