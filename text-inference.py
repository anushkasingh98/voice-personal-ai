import ollama
import json
import os
import math
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
MODELS = ["gemma4:26b", "qwen3.6:35b", "mistral-small:24b"]
TRANSCRIPT_PATH = "/Users/anushkasingh/Desktop/Code/Sundai/voice_may3_26/voice-personal-ai/transcript.txt"
CHUNK_SIZE_WORDS = 1500  # Approx 6-8 minutes of speech
OVERLAP_WORDS = 200      # 20% overlap to catch context across splits
CHUNK_SIZE_LINES = 50  # Number of lines per chunk
OVERLAP_LINES = 10     # Number of lines to repeat from the previous chunk

PROMPT_TEMPLATE = """
You are a project manager. Extract all tasks and action items from this meeting fragment.
Return the result EXCLUSIVELY in valid JSON. 
If no tasks are found in this specific fragment, return {'tasks': []}.

TRANSCRIPT FRAGMENT:
---
{chunk_text}
---
"""

def get_chunks(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks

def get_chunks_by_lines(text, chunk_size, overlap):
    """
    Splits text into chunks based on line count with a rolling overlap.
    """
    lines = text.splitlines()
    chunks = []
    
    # Ensure we don't get stuck in an infinite loop if overlap >= chunk_size
    step = max(1, chunk_size - overlap)
    
    for i in range(0, len(lines), step):
        # Slice the lines and join them back with newlines
        chunk = "\n".join(lines[i:i + chunk_size])
        chunks.append(chunk)
        
        # Stop if we've reached the end of the document
        if i + chunk_size >= len(lines):
            break
            
    return chunks

def process_with_model(model_name, chunks):
    all_tasks = []
    
    for i, chunk in enumerate(chunks):
        print(f"  [Chunk {i+1}/{len(chunks)}] Processing...")
        try:
            response = ollama.generate(
                model=model_name,
                prompt=PROMPT_TEMPLATE.format(chunk_text=chunk),
                format="json",
                options={
                    "temperature": 0.1, 
                    "num_ctx": 4096
                }
            )
            
            # Load the raw string into a Python dictionary
            raw_output = response.get('response', '{}')
            data = json.loads(raw_output)
            
            # DEFENSIVE CHECKS:
            # 1. If the model returned a list directly instead of {"tasks": []}
            if isinstance(data, list):
                chunk_tasks = data
            # 2. If it's a dict, safely get 'tasks', defaulting to an empty list
            elif isinstance(data, dict):
                chunk_tasks = data.get("tasks", [])
            else:
                chunk_tasks = []

            all_tasks.extend(chunk_tasks)
            
        except json.JSONDecodeError:
            print(f"  Error: Chunk {i+1} returned invalid JSON.")
        except Exception as e:
            print(f"  Error in chunk {i+1} with {model_name}: {e}")

    # Deduplication logic remains the same
    unique_tasks = {}
    for t in all_tasks:
        if isinstance(t, dict): # Ensure the task itself is a dictionary
            desc = t.get('task_description', '').lower().strip()
            speaker = t.get('speaker', 'unknown').lower().strip()
            key = f"{speaker}-{desc}"
            if desc and key not in unique_tasks:
                unique_tasks[key] = t
            
    return list(unique_tasks.values())

def main():
    if not os.path.exists(TRANSCRIPT_PATH):
        print(f"File {TRANSCRIPT_PATH} not found.")
        return

    with open(TRANSCRIPT_PATH, "r") as f:
        full_text = f.read()

    # Split transcript into overlapping windows
    chunks = get_chunks_by_lines(full_text, CHUNK_SIZE_LINES, OVERLAP_LINES)
    print(f"Transcript split into {len(chunks)} chunks.")

    for model in MODELS:
        print(f"\n>> STARTING MODEL: {model}")
        final_tasks = process_with_model(model, chunks)
        
        output_file = f"extracted_tasks_{model.replace(':', '_')}.json"
        with open(output_file, "w") as out:
            json.dump({"total_tasks": len(final_tasks), "tasks": final_tasks}, out, indent=2)
        
        print(f">> DONE. Saved {len(final_tasks)} unique tasks to {output_file}")

if __name__ == "__main__":
    main()