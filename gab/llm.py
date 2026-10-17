"""LLM backends with one interface: complete(system, user) -> text.

    anthropic   Anthropic Messages API (ANTHROPIC_API_KEY; model via --model)
    openai      any OpenAI-compatible chat endpoint, e.g. Ollama at http://localhost:11434/v1
    replay      replays recorded responses from a previous run (used by CI: no network, no key)

Only the standard library is used, so the benchmark adds no SDK dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Completion:
    text: str
    seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None


def _post(url: str, payload: dict, headers: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"content-type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def prompt_key(system: str, user: str) -> str:
    return hashlib.sha256((system + "\x00" + user).encode()).hexdigest()[:24]


class AnthropicLLM:
    def __init__(self, model: str):
        self.model = model
        self.key = os.environ["ANTHROPIC_API_KEY"]

    def complete(self, system: str, user: str) -> Completion:
        t0 = time.time()
        out = _post("https://api.anthropic.com/v1/messages",
                    {"model": self.model, "max_tokens": 1200, "temperature": 0, "system": system,
                     "messages": [{"role": "user", "content": user}]},
                    {"x-api-key": self.key, "anthropic-version": "2023-06-01"})
        text = "".join(b.get("text", "") for b in out.get("content", []))
        usage = out.get("usage", {})
        return Completion(text, time.time() - t0, usage.get("input_tokens"), usage.get("output_tokens"))


class OpenAICompatibleLLM:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.key = os.environ.get("OPENAI_API_KEY", "not-needed")

    def complete(self, system: str, user: str) -> Completion:
        t0 = time.time()
        out = _post(f"{self.base_url}/chat/completions",
                    {"model": self.model, "temperature": 0, "max_tokens": 1200,
                     "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                    {"authorization": f"Bearer {self.key}"})
        usage = out.get("usage", {})
        return Completion(out["choices"][0]["message"]["content"], time.time() - t0,
                          usage.get("prompt_tokens"), usage.get("completion_tokens"))


class ReplayLLM:
    """Returns the response recorded for the exact same prompt in a previous run."""

    def __init__(self, path: Path):
        self.responses = {}
        recorded_model = None
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                self.responses[rec["prompt_key"]] = rec["response"]
                recorded_model = rec.get("model", recorded_model)
        self.model = f"{recorded_model} (replayed)" if recorded_model else "replay"

    def complete(self, system: str, user: str) -> Completion:
        key = prompt_key(system, user)
        if key not in self.responses:
            raise KeyError(f"no recorded response for prompt {key}")
        return Completion(self.responses[key], 0.0)


class Recorder:
    """Wraps a backend and appends every (prompt, response) pair to a JSONL file."""

    def __init__(self, inner, path: Path):
        self.inner = inner
        self.model = getattr(inner, "model", "unknown")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def complete(self, system: str, user: str) -> Completion:
        c = self.inner.complete(system, user)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"prompt_key": prompt_key(system, user), "model": self.model,
                                "response": c.text}) + "\n")
        return c


def make_llm(backend: str, model: str | None, base_url: str | None, replay_path: Path | None):
    if backend == "anthropic":
        return AnthropicLLM(model or "claude-sonnet-4-5")
    if backend == "openai":
        return OpenAICompatibleLLM(model or "qwen2.5-coder:7b", base_url or "http://localhost:11434/v1")
    if backend == "replay":
        return ReplayLLM(replay_path)
    raise ValueError(f"unknown backend {backend!r}")
