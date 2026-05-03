# Run this once locally to diagnose
import ollama, json, re

PROMPT = """
You are a project manager. Extract all tasks and action items from this meeting fragment.
Return the result EXCLUSIVELY in valid JSON. 
If no tasks are found in this specific fragment, return {'tasks': []}.

TRANSCRIPT FRAGMENT:
---
[00.00s - 02.00s] Anushka: Hello, how are you?
---
"""

print("Sending prompt to model...")

response = ollama.generate(
    model="mistral-small:24b",
    prompt=PROMPT,
    format="json",
    options={"temperature": 0.1, "num_ctx": 4096}
)

print("TYPE:", type(response))
print("IS DICT:", isinstance(response, dict))
print("KEYS:", response.keys() if isinstance(response, dict) else dir(response))
raw = response.get('response', 'MISSING') if isinstance(response, dict) else getattr(response, 'response', 'MISSING')
print("RAW:", repr(raw[:300]))