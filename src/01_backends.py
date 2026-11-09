# ===================== MODEL BACKENDS + UTILITIES =====================
import json, os, re, time, random, threading, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class BackendError(Exception):
    pass


class OllamaBackend:
    """An open-weights model served by Ollama on the Colab GPU. JSON mode guarantees parseable output."""

    def __init__(self, model, host="http://localhost:11434", num_ctx=6144, max_tokens=400):
        self.model, self.host, self.num_ctx, self.max_tokens = model, host, num_ctx, max_tokens
        self.label = f"ollama:{model}"

    def chat(self, prompt, temperature=0.7, json_mode=True):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": self.num_ctx,
                        "num_predict": self.max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        last = None
        for attempt in range(5):
            try:
                r = requests.post(f"{self.host}/api/chat", json=payload, timeout=600)
                r.raise_for_status()
                return r.json()["message"]["content"]
            except Exception as e:  # server busy, model loading, etc.
                last = e
                time.sleep(3 * (attempt + 1))
        raise BackendError(f"Ollama failed after retries: {last}")


class ColabGeminiBackend:
    """Gemini through Colab's built-in google.colab.ai library (free tier, no key, Colab only)."""

    def __init__(self, model_name):
        from google.colab import ai  # noqa: only importable inside Colab
        self.ai, self.model = ai, model_name
        self.label = f"colab:{model_name.split('/')[-1]}"

    def chat(self, prompt, temperature=0.7, json_mode=True):
        last = None
        for attempt in range(7):
            try:
                out = self.ai.generate_text(prompt, model_name=self.model)
                return out if isinstance(out, str) else str(out)
            except Exception as e:  # usually a rate limit: back off and retry
                last = e
                time.sleep(min(90, 5 * 2 ** attempt) + random.random())
        raise BackendError(f"Colab Gemini failed after retries: {last}")


class OpenAICompatBackend:
    """Any OpenAI-compatible chat endpoint (Gemini API, Groq, OpenRouter, a local vLLM...)."""

    def __init__(self, base_url, api_key, model, max_tokens=400):
        self.base_url, self.api_key, self.model, self.max_tokens = base_url.rstrip("/"), api_key, model, max_tokens
        self.label = f"api:{model}"
        self._json_ok = True

    def chat(self, prompt, temperature=0.7, json_mode=True):
        last = None
        for attempt in range(7):
            payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": temperature, "max_tokens": self.max_tokens}
            if json_mode and self._json_ok:
                payload["response_format"] = {"type": "json_object"}
            try:
                r = requests.post(self.base_url + "/chat/completions", json=payload, timeout=180,
                                  headers={"Authorization": f"Bearer {self.api_key}"})
                if r.status_code == 400 and "response_format" in payload:
                    self._json_ok = False  # provider does not support JSON mode; rely on the prompt
                    continue
                if r.status_code in (429, 500, 502, 503, 504):
                    raise BackendError(f"HTTP {r.status_code}")
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                last = e
                time.sleep(min(90, 4 * 2 ** attempt) + random.random())
        raise BackendError(f"API failed after retries: {last}")


def parse_json(text):
    """Pull the first JSON object out of a model reply (handles code fences and chatter)."""
    if not isinstance(text, str):
        return None
    t = re.sub(r"```(?:json)?", "", text).strip()
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = t.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            c = t[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(t[start:i + 1])
                        return obj if isinstance(obj, dict) else None
                    except Exception:
                        break
        start = t.find("{", start + 1)
    return None


def as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "y", "1")
    return False


def run_parallel(fn, items, workers=4, desc=""):
    """Run fn over items with a thread pool; keeps input order; errors come back as dicts."""
    results = [None] * len(items)
    try:
        from tqdm.auto import tqdm
    except Exception:
        tqdm = None
    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
        done = as_completed(futs)
        if tqdm is not None and desc:
            done = tqdm(done, total=len(futs), desc=desc)
        for f in done:
            i = futs[f]
            try:
                results[i] = f.result()
            except Exception as e:
                results[i] = {"error": repr(e)}
    return results


class JsonlStore:
    """Append-only results file, so a Colab disconnect never loses finished trials."""

    def __init__(self, path):
        self.path, self.lock = path, threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def load(self):
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
        return out

    def done_ids(self):
        return {r["id"] for r in self.load() if "id" in r and not r.get("error")}

    def append(self, rec):
        with self.lock:
            with open(self.path, "a") as f:
                f.write(json.dumps(rec) + "\n")


def stable_seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)
