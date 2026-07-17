#!/usr/bin/env python3
"""sft_cgh2 代码改错服务：静态前端 + POST /repair。

输入:
  POST /repair  JSON {problem, buggy_code, feedback}
  模型: Qwen1.5-0.5B-Chat + sft_cgh2/outputs/qwen15_repair_lora

输出:
  {fixed_code, output, elapsed_sec}

用法:
  python sft_cgh2/scripts/serve_repair.py
  # → http://0.0.0.0:8081/sft_cgh2/frontend/
  # → POST http://0.0.0.0:8081/repair
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DPO_SCRIPTS = PROJECT_ROOT / "dpo" / "scripts"
DEFAULT_ADAPTER = PROJECT_ROOT / "sft_cgh2" / "outputs" / "qwen15_repair_lora"
DEFAULT_PORT = 8081

REPAIR_INSTRUCTION = (
    "Fix the buggy Python code so that it satisfies the programming task and "
    "passes the failing tests. Return only the corrected Python code."
)

for path in (PROJECT_ROOT, DPO_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mbpp_eval_dpo import apply_chat_template, load_model  # noqa: E402

INFERENCE_LOCK = threading.Lock()
_MODEL_BUNDLE: tuple | None = None


def get_model():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        adapter = Path(os.environ.get("REPAIR_ADAPTER", str(DEFAULT_ADAPTER)))
        print(f"[repair] Loading adapter: {adapter}", flush=True)
        _MODEL_BUNDLE = load_model(adapter, trust_remote_code=True)
        print("[repair] Model ready", flush=True)
    return _MODEL_BUNDLE


def build_user_content(problem: str, buggy_code: str, feedback: str) -> str:
    # Match LLaMA-Factory alpaca+qwen packing: instruction then input with a single newline.
    return (
        f"{REPAIR_INSTRUCTION}\n"
        "### Problem\n"
        f"{problem.strip()}\n\n"
        "### Buggy Code\n"
        "```python\n"
        f"{buggy_code.strip()}\n"
        "```\n\n"
        "### Failing Tests / Error Messages\n"
        f"{feedback.strip()}"
    )


def render_prompt(tokenizer, user_content: str) -> str:
    """Use the same chat template shape as offline predict (system + user)."""
    messages = [
        {
            "role": "system",
            "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.",
        },
        {"role": "user", "content": user_content},
    ]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return apply_chat_template(tokenizer, user_content)


def extract_code(text: str) -> str:
    text = (text or "").strip()
    fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced[0].strip()
    return text


def run_repair(problem: str, buggy_code: str, feedback: str, max_new_tokens: int = 768) -> dict:
    tokenizer, model, torch = get_model()
    user_content = build_user_content(problem, buggy_code, feedback)
    rendered = render_prompt(tokenizer, user_content)
    inputs = tokenizer([rendered], return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    start = time.perf_counter()
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.perf_counter() - start
    prompt_width = inputs["input_ids"].shape[1]
    raw = tokenizer.decode(output_ids[0][prompt_width:], skip_special_tokens=True)
    fixed = extract_code(raw)
    return {
        "fixed_code": fixed,
        "output": raw,
        "elapsed_sec": round(elapsed, 3),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[serve] {self.address_string()} {fmt % args}", flush=True)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path = unquote(self.path.split("?", 1)[0]).rstrip("/")
        if path != "/repair":
            self.send_json(404, {"error": "Not Found. Use POST /repair"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON"})
            return

        problem = str(payload.get("problem") or "").strip()
        buggy_code = str(payload.get("buggy_code") or "").strip()
        feedback = str(payload.get("feedback") or "").strip()
        if not problem or not buggy_code:
            self.send_json(400, {"error": "problem and buggy_code are required"})
            return

        max_new_tokens = int(payload.get("max_new_tokens", 768))
        try:
            with INFERENCE_LOCK:
                result = run_repair(problem, buggy_code, feedback, max_new_tokens=max_new_tokens)
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})
            return
        self.send_json(200, result)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path).rstrip("/") or "/"

        if path in {"/", "/sft_cgh2", "/sft_cgh2/"}:
            self.send_response(302)
            self.send_header("Location", "/sft_cgh2/frontend/")
            self.end_headers()
            return

        if path == "/v1/health":
            self.send_json(200, {"status": "ok", "service": "sft_cgh2_repair"})
            return

        super().do_GET()


def main() -> None:
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    gpu = os.environ.get("GPU_ID", "0")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", gpu)

    # Eager-load so the first /repair is fast and failures surface at startup.
    if os.environ.get("REPAIR_EAGER_LOAD", "1") == "1":
        get_model()

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Serving on http://0.0.0.0:{port}")
    print(f"Frontend: http://localhost:{port}/sft_cgh2/frontend/")
    print(f"API:      POST http://localhost:{port}/repair")
    print(f"GPU:      {os.environ.get('CUDA_VISIBLE_DEVICES')}")
    print("在前端「模型推理台」填入上述 /repair 地址，或留空用演示模式。")
    server.serve_forever()


if __name__ == "__main__":
    main()
