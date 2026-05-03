import ollama
import json
import os
import re
import time
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

# --- SCHEMA DEFINITION ---
class Task(BaseModel):
    speaker: str = Field(description="Name of the person responsible")
    task_description: str = Field(description="Specific actionable task")
    deadline: Optional[str] = Field(None, description="Timeframe if mentioned")
    priority: str = Field("Medium", description="High, Medium, or Low")

class MeetingExtraction(BaseModel):
    tasks: List[Task]

# --- CONFIGURATION ---
MODELS = ["qwen3.5:9b", "mistral-nemo:12b", "gemma4:e4b"]

TRANSCRIPT_PATH = "/Users/anushkasingh/Desktop/Code/Sundai/voice_may3_26/voice-personal-ai/transcript.txt"
CHUNK_SIZE_LINES = 50
OVERLAP_LINES = 10

PROMPT_TEMPLATE = """
This is a customer discovery call between a founder and a customer. Extract all tasks, promises and action items that any speaker commits to do from this meeting fragment.
Return the result EXCLUSIVELY in valid JSON. The JSON should be an object with a single key "tasks" which is a list of task objects. Each task object should have the following fields:
- "speaker": the name of the person responsible for the task (if identifiable, otherwise "unknown")
- "task_description": a specific description of the task or action item
- "deadline": any mentioned timeframe or deadline for the task (if mentioned, otherwise null)
- "priority": "High", "Medium", or "Low" based on the urgency implied in the conversation. If no tasks are found in this specific fragment, return an empty list for "tasks".

TRANSCRIPT FRAGMENT:
---
{chunk_text}
---
"""

# --- CHUNKING ---
def get_chunks_by_lines(text, chunk_size, overlap):
    lines = text.splitlines()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(lines), step):
        chunk = "\n".join(lines[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(lines):
            break
    return chunks

# --- RESPONSE PARSING ---
def extract_raw_text(response):
    """Handle both old dict-style and new object-style ollama responses."""
    if isinstance(response, dict):
        return response.get('response', '{}'), response
    return getattr(response, 'response', '{}'), response

def safe_parse_json(raw: str) -> dict:
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)
    raw = re.sub(r'^```[a-z]*\n?|```$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        return {}

def extract_token_counts(response) -> dict:
    """Extract token usage from ollama response (works for both dict and object)."""
    fields = ['prompt_eval_count', 'eval_count', 'eval_duration', 'prompt_eval_duration', 'load_duration', 'total_duration']
    result = {}
    for f in fields:
        if isinstance(response, dict):
            result[f] = response.get(f, None)
        else:
            result[f] = getattr(response, f, None)
    return result

# --- CORE PROCESSING ---
def process_with_model(model_name, chunks):
    all_tasks = []
    model_analytics = {
        "model": model_name,
        "start_time": datetime.now().isoformat(),
        "chunks": [],
        "totals": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "tasks_found": 0,
            "errors": 0,
            "wall_time_sec": 0.0,
        }
    }

    model_start = time.perf_counter()

    for i, chunk in enumerate(chunks):
        print(f"  [Chunk {i+1}/{len(chunks)}] Processing...")
        chunk_analytics = {
            "chunk_index": i + 1,
            "chunk_lines": chunk.count('\n') + 1,
            "chunk_chars": len(chunk),
        }
        chunk_start = time.perf_counter()

        try:
            response = ollama.generate(
                model=model_name,
                prompt=PROMPT_TEMPLATE.format(chunk_text=chunk),
                format="json",
                options={"temperature": 0.1, "num_ctx": 4096}
            )

            chunk_wall_time = time.perf_counter() - chunk_start
            raw_output, raw_response = extract_raw_text(response)
            token_info = extract_token_counts(raw_response)

            print(f"    DEBUG raw[:100]: {repr(raw_output[:100])}")

            data = safe_parse_json(raw_output)

            if isinstance(data, list):
                chunk_tasks = data
            elif isinstance(data, dict):
                chunk_tasks = data.get("tasks") or []
            else:
                chunk_tasks = []

            print(f"    Found {len(chunk_tasks)} tasks | "
                  f"tokens in/out: {token_info.get('prompt_eval_count','?')}/{token_info.get('eval_count','?')} | "
                  f"time: {chunk_wall_time:.1f}s")

            all_tasks.extend(chunk_tasks)

            # Per-chunk analytics
            prompt_tokens = token_info.get('prompt_eval_count') or 0
            completion_tokens = token_info.get('eval_count') or 0
            chunk_analytics.update({
                "status": "ok",
                "wall_time_sec": round(chunk_wall_time, 3),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "tasks_found": len(chunk_tasks),
                # Ollama reports durations in nanoseconds
                "ollama_load_duration_ms": round((token_info.get('load_duration') or 0) / 1e6, 2),
                "ollama_prompt_eval_duration_ms": round((token_info.get('prompt_eval_duration') or 0) / 1e6, 2),
                "ollama_eval_duration_ms": round((token_info.get('eval_duration') or 0) / 1e6, 2),
                "ollama_total_duration_ms": round((token_info.get('total_duration') or 0) / 1e6, 2),
                "tokens_per_sec": round(completion_tokens / chunk_wall_time, 1) if chunk_wall_time > 0 else None,
            })

            # Accumulate totals
            model_analytics["totals"]["prompt_tokens"] += prompt_tokens
            model_analytics["totals"]["completion_tokens"] += completion_tokens
            model_analytics["totals"]["total_tokens"] += prompt_tokens + completion_tokens
            model_analytics["totals"]["tasks_found"] += len(chunk_tasks)

        except Exception as e:
            chunk_wall_time = time.perf_counter() - chunk_start
            print(f"  Error in chunk {i+1} with {model_name}: {e}")
            chunk_analytics.update({
                "status": "error",
                "error": str(e),
                "wall_time_sec": round(chunk_wall_time, 3),
            })
            model_analytics["totals"]["errors"] += 1

        model_analytics["chunks"].append(chunk_analytics)

    model_wall_time = time.perf_counter() - model_start
    model_analytics["totals"]["wall_time_sec"] = round(model_wall_time, 3)
    model_analytics["totals"]["avg_tokens_per_sec"] = round(
        model_analytics["totals"]["completion_tokens"] / model_wall_time, 1
    ) if model_wall_time > 0 else None
    model_analytics["end_time"] = datetime.now().isoformat()

    # Deduplication
    unique_tasks = {}
    for t in all_tasks:
        if isinstance(t, dict):
            desc = t.get('task_description', '').lower().strip()
            speaker = t.get('speaker', 'unknown').lower().strip()
            key = f"{speaker}-{desc}"
            if desc and key not in unique_tasks:
                unique_tasks[key] = t

    model_analytics["totals"]["unique_tasks_after_dedup"] = len(unique_tasks)

    return list(unique_tasks.values()), model_analytics


# --- MAIN ---
def main():
    if not os.path.exists(TRANSCRIPT_PATH):
        print(f"File {TRANSCRIPT_PATH} not found.")
        return

    with open(TRANSCRIPT_PATH, "r") as f:
        full_text = f.read()

    run_start = time.perf_counter()
    run_start_time = datetime.now().isoformat()

    chunks = get_chunks_by_lines(full_text, CHUNK_SIZE_LINES, OVERLAP_LINES)
    print(f"Transcript split into {len(chunks)} chunks.\n")

    all_analytics = {
        "run_start": run_start_time,
        "transcript_path": TRANSCRIPT_PATH,
        "transcript_chars": len(full_text),
        "transcript_lines": full_text.count('\n') + 1,
        "num_chunks": len(chunks),
        "chunk_size_lines": CHUNK_SIZE_LINES,
        "overlap_lines": OVERLAP_LINES,
        "models": []
    }

    for model in MODELS:
        print(f"\n>> STARTING MODEL: {model}")
        final_tasks, model_analytics = process_with_model(model, chunks)

        output_file = f"extracted_tasks_{model.replace(':', '_')}.json"
        with open(output_file, "w") as out:
            json.dump({"total_tasks": len(final_tasks), "tasks": final_tasks}, out, indent=2)

        print(f">> DONE. Saved {len(final_tasks)} unique tasks to {output_file}")
        print(f"   Total tokens: {model_analytics['totals']['total_tokens']} | "
              f"Wall time: {model_analytics['totals']['wall_time_sec']}s | "
              f"Avg speed: {model_analytics['totals'].get('avg_tokens_per_sec', '?')} tok/s")

        all_analytics["models"].append(model_analytics)

    # Summary comparison table across models
    all_analytics["run_end"] = datetime.now().isoformat()
    all_analytics["total_wall_time_sec"] = round(time.perf_counter() - run_start, 3)
    all_analytics["summary"] = [
        {
            "model": m["model"],
            "wall_time_sec": m["totals"]["wall_time_sec"],
            "total_tokens": m["totals"]["total_tokens"],
            "prompt_tokens": m["totals"]["prompt_tokens"],
            "completion_tokens": m["totals"]["completion_tokens"],
            "avg_tokens_per_sec": m["totals"].get("avg_tokens_per_sec"),
            "tasks_found": m["totals"]["tasks_found"],
            "unique_tasks": m["totals"]["unique_tasks_after_dedup"],
            "errors": m["totals"]["errors"],
        }
        for m in all_analytics["models"]
    ]

    analytics_file = "analytics.json"
    with open(analytics_file, "w") as f:
        json.dump(all_analytics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Analytics saved to {analytics_file}")
    print(f"{'='*60}")
    print(f"{'Model':<25} {'Time(s)':>8} {'Tokens':>8} {'tok/s':>7} {'Tasks':>6} {'Errors':>7}")
    print(f"{'-'*60}")
    for s in all_analytics["summary"]:
        print(f"{s['model']:<25} {s['wall_time_sec']:>8.1f} {s['total_tokens']:>8} "
              f"{str(s['avg_tokens_per_sec'] or '?'):>7} {s['unique_tasks']:>6} {s['errors']:>7}")

if __name__ == "__main__":
    main()