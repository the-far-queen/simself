"""
call_minimax.py — MiniMax API call surface for the self-prompt loop.

This is not a generic SDK. The contract is:

  response = complete(prompt: str, *, model: str = "MiniMax-M3",
                      system: str | None = None, max_tokens: int = 4096,
                      temperature: float = 0.2) -> MiniMaxResponse

The model is told (via the system prompt) to respond with a unified diff
only — no prose. self_prompt.py formats the prompt; apply_patch.py
parses the diff. This module only handles the HTTP round-trip + auth
+ retry + streaming.

Auth:
  The MiniMax API key is read from $MINIMAX_API_KEY (env var). The
  base URL is $MINIMAX_BASE_URL (default https://api.minimax.io/v1).
  Override model with $MINIMAX_MODEL (default MiniMax-M3).

Retry:
  Exponential backoff on 429 / 5xx. No retry on 4xx other than 429.
  Default max attempts: 3. Default base delay: 2.0s.

Streaming:
  The response is collected fully before return. We do not stream the
  diff into apply_patch.py because the parser requires the whole diff
  to detect its boundaries.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


DEFAULT_BASE_URL = "https://api.minimax.io/v1"
DEFAULT_MODEL = "MiniMax-M3"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY = 2.0


@dataclass
class MiniMaxResponse:
    """The model's reply to a self-prompt."""
    text: str                    # the raw response text (a unified diff)
    model: str                   # model that produced it
    finish_reason: str           # "stop" | "length" | ...
    prompt_tokens: int = 0       # usage.prompt_tokens
    completion_tokens: int = 0   # usage.completion_tokens
    total_tokens: int = 0
    elapsed_seconds: float = 0.0


class MiniMaxError(RuntimeError):
    """Raised for non-retryable API errors or exhausted retries."""
    def __init__(self, message: str, *, status: Optional[int] = None,
                 body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _read_api_key() -> str:
    """Read MINIMAX_API_KEY from env. Falls back to ~/.minimax.env (one-line KEY=value)."""
    key = os.environ.get("MINIMAX_API_KEY")
    if key:
        return key
    # Fall back: a dotenv-style file in the user's home.
    env_path = os.path.join(os.path.expanduser("~"), ".minimax.env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise MiniMaxError(
        "MINIMAX_API_KEY not set. export it or add to ~/.minimax.env"
    )


def complete(prompt: str, *,
             model: Optional[str] = None,
             system: Optional[str] = None,
             max_tokens: Optional[int] = None,
             temperature: Optional[float] = None,
             max_attempts: int = DEFAULT_MAX_ATTEMPTS,
             base_delay: float = DEFAULT_BASE_DELAY,
             timeout: float = 120.0) -> MiniMaxResponse:
    """Send a prompt to the MiniMax API and return the response.

    Args:
        prompt: The user-role message. The self-prompt loop assembles this
            from repo state + goal + constraints.
        model: Defaults to $MINIMAX_MODEL or "MiniMax-M3".
        system: Optional system-role instruction. The default system prompt
            tells the model to respond with a unified diff only.
        max_tokens: Defaults to 4096. Diff patches are typically 200-2000 tokens.
        temperature: Defaults to 0.2 (low — we want deterministic patches).
        max_attempts: Retry budget for 429 / 5xx.
        base_delay: Seconds; doubled bound per.
        timeout: Per-request HTTP timeout.

    Returns:
        MiniMaxResponse with .text (the diff), .model, .finish_reason, .*_tokens.

    Raises:
        MiniMaxError for auth failure, 4xx other than 429, or exhausted retries.
    """
    model = model or os.environ.get("MINIMAX_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
    temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE

    if system is None:
        system = (
            "You are a code-patch assistant for the simself/fieldcore repositories. "
            "The user will provide a 5-field prompt (repository state, test surface, "
            "goal, constraints, plan field). Respond with a unified diff ONLY. No "
            "prose, no explanation, no markdown formatting outside the diff. "
            "If the goal cannot be satisfied within the constraints, respond with "
            "exactly the string NO_DIFF and nothing else."
        )

    api_key = _read_api_key()
    url = f"{base_url}/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "simself-autocode/0.1",
    }

    last_err: Optional[Exception] = None
    elapsed = 0.0
    payload: Optional[dict] = None
    for attempt in range(1, max_attempts + 1):
        t0 = time.perf_counter()
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            elapsed = time.perf_counter() - t0
            last_err = None
            break
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")[:1000]
            except Exception:
                pass
            last_err = MiniMaxError(
                f"HTTP {e.code}: {body_text or e.reason}",
                status=e.code, body=body_text,
            )
            # Retry on 429 / 5xx; everything else is fatal.
            if e.code not in (429, 500, 502, 503, 504):
                raise last_err from e
        except urllib.error.URLError as e:
            last_err = MiniMaxError(f"URL error: {e.reason}")
            # Network errors are retryable.
        except (TimeoutError, json.JSONDecodeError) as e:
            last_err = MiniMaxError(f"Transport: {e}")
            # Transport errors are retryable.

        # Decide: retry or give up?
        if attempt >= max_attempts:
            raise last_err
        delay = base_delay * (2 ** (attempt - 1))
        sys.stderr.write(
            f"[call_minimax] attempt {attempt}/{max_attempts} failed: "
            f"{last_err}. retrying in {delay:.1f}s\n"
        )
        time.sleep(delay)

    # After the loop, payload is set (success path) or we already raised.
    if payload is None:
        raise MiniMaxError("call_minimax: no payload after retry loop")

    # Parse the chat-completions payload.
    try:
        choice = payload["choices"][0]
        text = choice["message"]["content"]
        finish_reason = choice.get("finish_reason", "stop")
        usage = payload.get("usage", {})
        return MiniMaxResponse(
            text=text,
            model=payload.get("model", model),
            finish_reason=finish_reason,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
            elapsed_seconds=elapsed,
        )
    except (KeyError, IndexError, TypeError) as e:
        raise MiniMaxError(
            f"Malformed MiniMax response: {e}; payload={json.dumps(payload)[:500]}"
        ) from e


# --- CLI for ad-hoc testing ----------------------------------------------

def _cli():
    import argparse
    p = argparse.ArgumentParser(description="Send a prompt to the MiniMax API.")
    p.add_argument("prompt", help="Prompt text (or '-' for stdin)")
    p.add_argument("--model", default=None)
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--system", default=None)
    args = p.parse_args()
    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    r = complete(
        prompt,
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        system=args.system,
    )
    sys.stdout.write(r.text)
    if not r.text.endswith("\n"):
        sys.stdout.write("\n")
    sys.stderr.write(
        f"[call_minimax] model={r.model} finish={r.finish_reason} "
        f"tokens={r.total_tokens} ({r.prompt_tokens}+{r.completion_tokens}) "
        f"elapsed={r.elapsed_seconds:.2f}s\n"
    )


if __name__ == "__main__":
    _cli()