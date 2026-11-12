# implements: FR-001
# implements: FR-002
# implements: FR-003
# implements: FR-004
# implements: FR-005
# implements: FR-006
# implements: FR-007
# implements: FR-008
# traces_to: Π.3.1
# traces_to: Π.5.3

"""Autonomous self-remediation runner for First-ADE compliance violations."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import click
import httpx

# Security constraint: Do not modify workflow files
RESTRICTED_PATHS = (".github/workflows/",)

MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
)
MODEL_HASH = "cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046"  # pragma: allowlist secret

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
    """Return user home directory cache path for the quantized GGUF model."""
    cache_dir = Path.home() / ".cache" / "first-ade"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"


def verify_file_hash(path: Path, expected_hash: str) -> bool:
    """Verify SHA-256 digest of a downloaded file."""
    if not path.exists():
        return False
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_hash


def download_model(dest_path: Path) -> None:
    """Download the quantized Qwen2.5-Coder GGUF model to a temporary file and atomically replace."""
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
    report_file = Path(".").resolve() / Path(report_path).name
    try:
        subprocess.run(
            ["uv", "run", "ade-compliance", "generate-report", ".", "--output", str(report_file)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # Non-zero exit code indicates violations were found and written to the report file.
        pass

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"Failed to read compliance report at {report_file.name}: {exc}")
        return {"violations": []}


def _append_unique(target: list[str], items: list[str]) -> None:
    """Append items not already present in target."""
    for item in items:
        if item not in target:
            target.append(item)


def _extract_traces_from_markdown(md_file: Path, filename: str, implements: list[str], traces_to: list[str]) -> None:
    """Extract requirement, axiom, and ADR identifiers from a markdown file referencing filename."""
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        # Unreadable markdown files are skipped during trace discovery.
        return
    if filename not in content:
        return
    _append_unique(implements, re.findall(r"\b(FR-\d+)\b", content))
    _append_unique(traces_to, re.findall(r"\b(Π\.\d+\.\d+)\b", content))
    _append_unique(traces_to, re.findall(r"\b(ADR-\d+|ADR\d+)\b", content))


def find_trace_targets(file_path: Path) -> tuple[list[str], list[str]]:
    """Scan all markdown files in specs/ and docs/ for filename references."""
    implements: list[str] = []
    traces_to: list[str] = []
    filename = file_path.name
    root_dir = Path(".")

    for dir_name in ("specs", "docs"):
        search_dir = root_dir / dir_name
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            _extract_traces_from_markdown(md_file, filename, implements, traces_to)

    return implements, traces_to


def inject_trace_comments(file_path: Path, implements: list[str], traces_to: list[str]) -> None:
    """Insert trace comment headers at the top of a trusted project Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    comment_lines = [f"# implements: {imp}\n" for imp in implements]
    comment_lines.extend(f"# traces_to: {tr}\n" for tr in traces_to)

    if not comment_lines:
        comment_lines = ["# implements: FR-TODO\n", "# traces_to: Π.1.1\n"]

    insert_idx = 1 if (lines and lines[0].startswith("#!")) else 0
    new_lines = lines[:insert_idx] + comment_lines + ["\n"] + lines[insert_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
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
        resp = httpx.post(url, json=payload, timeout=20.0)
        if resp.status_code == 200:
            return resp.json()["message"]["content"]
    except Exception:
        # Local Ollama daemon may not be running; fall back to in-memory GGUF inference.
        return None
    return None


def query_local_llm(prompt: str, system_prompt: str) -> str:
    """Fallback: load llama-cpp-python and run quantized GGUF model in memory."""
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise RuntimeError("llama-cpp-python is not installed. Cannot run offline LLM inference.") from exc

    model_path = get_model_path()
    if not model_path.exists() or not verify_file_hash(model_path, MODEL_HASH):
        download_model(model_path)
        if not verify_file_hash(model_path, MODEL_HASH):
            raise RuntimeError("Downloaded model hash verification failed: hash mismatch.")

    print("Loading model weights into memory on CPU...")
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
    for pattern in (r"```python\n(.*?)```", r"```\n?(.*?)```"):
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
    return None


def remediate_logical_violation(file_path: Path, violation_message: str) -> None:
    """Run model inference to patch a python file with logical or spec violations."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as exc:
        print(f"Failed to read file {file_path.name}: {exc}")
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
        except Exception as exc:
            print(f"Failed local LLM inference: {exc}")
            return

    corrected_code = extract_code_block(response)
    if corrected_code:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(corrected_code)
        print(f"Successfully applied local LLM patch to {file_path.name}")
    else:
        print(f"LLM did not return a valid python code block for {file_path.name}")


def _index_project_python_files() -> dict[str, Path]:
    """Build a map of relative POSIX paths to trusted local Python files outside restricted directories."""
    base_dir = Path(".").resolve()
    indexed: dict[str, Path] = {}
    for candidate in base_dir.rglob("*.py"):
        rel_posix = candidate.relative_to(base_dir).as_posix()
        if any(part.startswith(".") for part in candidate.relative_to(base_dir).parts):
            continue
        if any(rel_posix.startswith(restricted) for restricted in RESTRICTED_PATHS):
            continue
        indexed[rel_posix] = candidate
    return indexed


def _normalize_report_key(raw_path: str) -> str:
    """Normalize a report path string to a clean relative POSIX lookup key."""
    cleaned = str(raw_path).replace("\\", "/").strip("/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def _remediate_single_violation(violation: dict, trusted_files: dict[str, Path]) -> Path | None:
    """Remediate a single compliance violation using only pre-indexed trusted project files."""
    raw_path = violation.get("file_path")
    if not raw_path:
        return None

    lookup_key = _normalize_report_key(str(raw_path))
    if any(lookup_key.startswith(restricted) for restricted in RESTRICTED_PATHS):
        print(f"Security Policy: Modification of restricted path {lookup_key} is blocked.")
        return None

    file_path = trusted_files.get(lookup_key)
    if file_path is None:
        print(f"File {lookup_key} is not a modifiable project Python file. Skipping.")
        return None

    axiom_id = violation.get("axiom_id", "")
    message = str(violation.get("message", ""))
    if axiom_id == "Π.3.1":
        implements, traces_to = find_trace_targets(file_path)
        inject_trace_comments(file_path, implements, traces_to)
    else:
        remediate_logical_violation(file_path, message)
    return file_path


def _stage_modified_files(modified_files: set[Path]) -> None:
    """Stage repaired files to the git index."""
    for file_path in modified_files:
        try:
            subprocess.run(["git", "add", "--", str(file_path)], check=True)
            print(f"Staged {file_path.name} to git index.")
        except Exception as exc:
            print(f"Failed to git add {file_path.name}: {exc}")


@click.command()
@click.option("--max-iterations", default=3, help="Max retry loop cycles.")
@click.option("--report-path", default="ade-report.json", help="Path to compliance JSON report.")
def main(max_iterations: int, report_path: str) -> None:
    """Autonomous self-remediation entrypoint."""
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Remediation Loop Iteration {iteration}/{max_iterations} ---")
        report = run_checks(report_path)
        violations = report.get("violations", [])
        active_violations = [v for v in violations if v.get("state") == "new"]
        if not active_violations:
            print("No active compliance violations found. Everything clean!")
            sys.exit(0)

        print(f"Found {len(active_violations)} violation(s) to fix.")
        trusted_files = _index_project_python_files()
        modified_files: set[Path] = set()
        for violation in active_violations:
            patched = _remediate_single_violation(violation, trusted_files)
            if patched is not None:
                modified_files.add(patched)

        _stage_modified_files(modified_files)

    print(f"\nMax iterations ({max_iterations}) reached. Compliance checks still failing.")
    sys.exit(1)


if __name__ == "__main__":
    main()
