"""
lmstudio_openai_client.py — OpenAI-compatible client for LM Studio.

**Source:** `C:\\Users\\Admin\\Downloads\\11.py` (Bobby paste 2026-09-17)
**Ingested:** 2026-09-17T09:57:22
**Where:** simself/src/tools/

Bobby's local LLM recipe — uses LM Studio's OpenAI-compatible API on
localhost:1234. Compatible with any OpenAI client library.

This complements the llama.cpp recipe in
`simself/src/research/local-llm-recipe-2026-09-11.md` (per the holomem).
Both are Bobby's local-model options; use whichever fits the use case:

- LM Studio (this file): OpenAI-compatible API, easy to swap models,
  GUI-driven. Best for: quick experimentation, hosted workflows.
- llama.cpp (the recipe): direct binary, command-line, max control.
  Best for: production + finetuning research.

LM Studio is already installed on Bobby's PC (verified 2026-09-17).
"""

from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1/chat/completions",
    api_key="sk-no-key-required"   # can be anything
)

response = client.chat.completions.create(
    model="qwen2.5-coder-7b",   # or just leave as "any"
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=1024
)

print(response.choices[0].message.content)
