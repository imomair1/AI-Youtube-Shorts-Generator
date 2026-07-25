"""Local LLM backend — Ollama (default), OpenAI, or Gemini, selected by LLM_PROVIDER."""
from ..config import (
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_MODEL,
    require_gemini_key,
    require_openai_key,
)


def call_ollama_llm(prompt: str) -> str:
    """Ollama backend — fully local, no API key required.

    Connects to a local Ollama server (default http://localhost:11434).
    Recommended models: qwen2.5:7b, llama3.1:8b, mistral:7b, gemma2:9b.
    """
    try:
        import ollama as ollama_lib  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "ollama is required for LLM_PROVIDER=ollama. Install it with:\n"
            "    pip install ollama"
        ) from e

    client = ollama_lib.Client(host=OLLAMA_BASE_URL)

    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.7,
                "num_predict": 8192,
            },
            format="json",
        )
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            raise RuntimeError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running:\n"
                "    ollama serve\n"
                "Then pull a model:\n"
                f"    ollama pull {OLLAMA_MODEL}"
            ) from e
        if "not found" in error_msg.lower() or "model" in error_msg.lower():
            raise RuntimeError(
                f"Ollama model '{OLLAMA_MODEL}' not found. Pull it first:\n"
                f"    ollama pull {OLLAMA_MODEL}"
            ) from e
        raise

    return response["message"]["content"] or ""


def call_openai_llm(prompt: str) -> str:
    """OpenAI Chat Completions backend used by --mode local."""
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "openai is required for --mode local. Install it with:\n"
            "    pip install -r requirements-local.txt"
        ) from e

    client = OpenAI(api_key=require_openai_key())
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def call_gemini_llm(prompt: str) -> str:
    """Gemini backend used by --mode local when LLM_PROVIDER=gemini."""
    try:
        from google import genai  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "google-genai is required for LLM_PROVIDER=gemini. Install it with:\n"
            "    pip install -r requirements-local.txt"
        ) from e

    client = genai.Client(api_key=require_gemini_key())
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
        },
    )
    return response.text or ""


def call_local_llm(prompt: str) -> str:
    """Dispatch to the configured local LLM provider."""
    provider = (LLM_PROVIDER or "ollama").strip().lower()
    if provider == "ollama":
        return call_ollama_llm(prompt)
    if provider == "openai":
        return call_openai_llm(prompt)
    if provider == "gemini":
        return call_gemini_llm(prompt)
    raise RuntimeError(
        f"Unknown LLM_PROVIDER={provider!r}. Use 'ollama', 'openai', or 'gemini'."
    )
