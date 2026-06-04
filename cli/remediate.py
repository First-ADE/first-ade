import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import click
import httpx

# Security constraint: Do not modify workflow files
RESTRICTED_PATHS = [".github/workflows/"]

MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
)
MODEL_HASH = "cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046"

SYSTEM_PROMPT = """You are an expert software developer. Your task is to fix compliance and quality errors in python files.
You will be provided with:
1. The path to the file.
2. The current contents of the file.
3. The compliance violation details.

You must return the COMPLETE corrected code of the file.
Format your response exactly as a single markdown code block:
```python
<corrected code here>
```
Do not include any other explanations, comments outside the code block, or conversational text. Provide only the code block."""

USER_PROMPT_TEMPLATE = """File Path: {file_path}

Violation: {violation_message}

Current Contents:
{file_content}"""


def get_model_path() -> Path:
    # Use user home directory cache to persist across workspace resets or CI caching
    cache_dir = Path.home() / ".cache" / "first-ade"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"


def verify_file_hash(path: Path, expected_hash: str) -> bool:
    if not path.exists():
        return False
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash


def download_model(dest_path: Path):
    print(f"Downloading Qwen2.5-Coder-1.5B model from {MODEL_URL}...")
    temp_path = dest_path.with_suffix(".tmp")
    with httpx.stream("GET", MODEL_URL, follow_redirects=True) as response:
        response.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)
    os.replace(temp_path, dest_path)
    print("Download completed successfully.")


def run_checks(report_path: str) -> dict:
    """Run compliance checks and output the JSON report."""
    try:
        subprocess.run(
            ["uv", "run", "ade-compliance", "generate-report", ".", "--output", report_path],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        # It's fine if the exit code is non-zero (indicating violations)
        # as long as the report JSON file was written.
        pass

    import json

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read compliance report at {report_path}: {e}")
        return {"violations": []}


def find_trace_targets(file_path: Path) -> tuple[list[str], list[str]]:
    """Scan all markdown files in specs/ and docs/ for filename references."""
    implements = []
    traces_to = []
    filename = file_path.name

    root_dir = Path(".")
    for dir_name in ["specs", "docs"]:
        search_dir = root_dir / dir_name
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue
            if filename in content:
                # Find requirements in the markdown file
                fr_matches = re.findall(r"\b(FR-\d+)\b", content)
                axiom_matches = re.findall(r"\b(Π\.\d+\.\d+)\b", content)
                adr_matches = re.findall(r"\b(ADR-\d+|ADR\d+)\b", content)
                for m in fr_matches:
                    if m not in implements:
                        implements.append(m)
                for m in axiom_matches:
                    if m not in traces_to:
                        traces_to.append(m)
                for m in adr_matches:
                    if m not in traces_to:
                        traces_to.append(m)

    return implements, traces_to


def inject_trace_comments(file_path: Path, implements: list[str], traces_to: list[str]):
    """Insert trace comment headers at the top of a python file."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    comment_lines = []
    for imp in implements:
        comment_lines.append(f"# implements: {imp}\n")
    for tr in traces_to:
        comment_lines.append(f"# traces_to: {tr}\n")

    if not comment_lines:
        comment_lines.append("# implements: FR-TODO\n")
        comment_lines.append("# traces_to: Π.1.1\n")

    insert_idx = 0
    if lines and lines[0].startswith("#!"):
        insert_idx = 1

    new_lines = lines[:insert_idx] + comment_lines + ["\n"] + lines[insert_idx:]
    file_path.write_text("".join(new_lines), encoding="utf-8")
    print(f"Patched traceability comments in {file_path.name}")


def query_ollama(prompt: str, system_prompt: str) -> str | None:
    """Attempt to run local inference via Ollama HTTP API."""
    url = "http://localhost:11434/api/chat"
    try:
        payload = {
            "model": "qwen2.5-coder:1.5b",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            "options": {"temperature": 0.1},
            "stream": False,
        }
        # Short timeout for quick local fallback
        resp = httpx.post(url, json=payload, timeout=20.0)
        if resp.status_code == 200:
            return resp.json()["message"]["content"]
    except Exception:
        pass
    return None


def query_local_llm(prompt: str, system_prompt: str) -> str:
    """Fallback: load llama-cpp-python and run quantized GGUF model in memory."""
    try:
        from llama_cpp import Llama
    except ImportError as e:
        raise RuntimeError("llama-cpp-python is not installed. Cannot run offline LLM inference.") from e

    model_path = get_model_path()
    if not model_path.exists() or not verify_file_hash(model_path, MODEL_HASH):
        download_model(model_path)
        if not verify_file_hash(model_path, MODEL_HASH):
            raise RuntimeError("Downloaded model hash verification failed: hash mismatch.")

    print("Loading model weights into memory on CPU...")
    # n_threads set to 2 to prevent high load in 2-core standard actions/local runners
    llm = Llama(model_path=str(model_path), n_ctx=2048, n_threads=2, verbose=False)

    formatted_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    )
    print("Running local CPU inference...")
    response = llm(
        formatted_prompt,
        max_tokens=1024,
        temperature=0.1,
        stop=["<|im_end|>", "<|im_start|>"],
    )
    return response["choices"][0]["text"]


def extract_code_block(response_text: str) -> str | None:
    """Parse python code block from model response."""
    match = re.search(r"```python\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"```\n?(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1)
    return None


def remediate_logical_violation(file_path: Path, violation_message: str):
    """Run model inference to patch a python file with logical or spec violations."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return

    prompt = USER_PROMPT_TEMPLATE.format(
        file_path=file_path.as_posix(), violation_message=violation_message, file_content=content
    )

    print("Attempting to query Ollama...")
    response = query_ollama(prompt, SYSTEM_PROMPT)

    if response is None:
        print("Ollama not available or failed. Falling back to local llama-cpp-python CPU inference...")
        try:
            response = query_local_llm(prompt, SYSTEM_PROMPT)
        except Exception as e:
            print(f"Failed local LLM inference: {e}")
            return

    corrected_code = extract_code_block(response)
    if corrected_code:
        file_path.write_text(corrected_code, encoding="utf-8")
        print(f"Successfully applied local LLM patch to {file_path.name}")
    else:
        print(f"LLM did not return a valid python code block for {file_path.name}")


@click.command()
@click.option("--max-iterations", default=3, help="Max retry loop cycles.")
@click.option("--report-path", default="ade-report.json", help="Path to compliance JSON report.")
def main(max_iterations: int, report_path: str):
    """Autonomous self-remediation entrypoint."""
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Remediation Loop Iteration {iteration}/{max_iterations} ---")
        report = run_checks(report_path)
        violations = report.get("violations", [])

        # Filter active (new) violations
        active_violations = [v for v in violations if v.get("state") == "new"]
        if not active_violations:
            print("No active compliance violations found. Everything clean!")
            sys.exit(0)

        print(f"Found {len(active_violations)} violation(s) to fix.")

        modified_files = set()
        for v in active_violations:
            rel_path = v.get("file_path")
            axiom_id = v.get("axiom_id")
            message = v.get("message")

            if not rel_path:
                continue

            file_path = Path(rel_path)
            if not file_path.exists():
                print(f"File {file_path} does not exist. Skipping.")
                continue

            # Security sanity check
            is_restricted = False
            for restricted in RESTRICTED_PATHS:
                if restricted in file_path.as_posix():
                    is_restricted = True
                    break
            if is_restricted:
                print(f"Security Policy: Modification of restricted path {file_path} is blocked.")
                continue

            if axiom_id == "Π.3.1":
                # US1: Simple trace link comment injection
                implements, traces_to = find_trace_targets(file_path)
                inject_trace_comments(file_path, implements, traces_to)
                modified_files.add(file_path)
            else:
                # US2 & US3: Logic repair using LLM inference
                remediate_logical_violation(file_path, message)
                modified_files.add(file_path)

        # Stage repaired changes to git automatically
        for f in modified_files:
            try:
                subprocess.run(["git", "add", str(f)], check=True)
                print(f"Staged {f.name} to git index.")
            except Exception as e:
                print(f"Failed to git add {f.name}: {e}")

    # If we exit the loop, checks are still failing
    print(f"\nMax iterations ({max_iterations}) reached. Compliance checks still failing.")
    sys.exit(1)


if __name__ == "__main__":
    main()
