# 🎙️ LooqBaq

Sundai Hackathon with RedHat

**LooqBaq** is a local-first meeting intelligence tool that transcribes audio/video recordings, identifies who said what, and automatically extracts action items — all running on your machine with no data sent to the cloud.

Built for founders and teams who want a structured record of every conversation without the privacy tradeoff.

---

## What it does

1. **Speaker Diarization** — Uses [Pyannote](https://github.com/pyannote/pyannote-audio) to detect and separate individual speakers in a recording.
2. **Transcription** — Runs [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (`distil-large-v3`) to transcribe speech to text with timestamps.
3. **Alignment** — Merges the diarization and transcription outputs so each line of the transcript is attributed to the right speaker.
4. **Task Extraction** — Chunks the transcript and passes it through local LLMs via [Ollama](https://ollama.com/) to pull out action items, owners, deadlines, and priority levels.
5. **Analytics** — Benchmarks multiple LLMs side-by-side on token usage, speed, task yield, and accuracy.
6. **Streamlit UI** — A clean light-mode web app for uploading recordings and reviewing results.

---

## Project structure

```
looqbaq/
├── app.py                  # Streamlit UI (upload + analytics dashboard)
├── main.py                 # Diarization + transcription pipeline
├── text-inference.py       # LLM-based task extraction + benchmarking
├── transcript.txt          # Output: timestamped, speaker-labelled transcript
├── extracted_tasks_*.json  # Output: tasks per model
├── analytics.json          # Output: full benchmarking data
└── local_pyannote_model/
    └── config.yaml         # Pyannote model loaded from disk (no internet required)
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- ffmpeg (`brew install ffmpeg` on Mac)
- A Hugging Face account with access to the [Pyannote speaker diarization model](https://huggingface.co/pyannote/speaker-diarization-3.1)

### 1. Install dependencies

```bash
pip install faster-whisper pyannote.audio torch streamlit ollama pydantic
```

### 2. Download the Pyannote model locally

After accepting the model terms on Hugging Face, download it and point `local_pyannote_model/config.yaml` to your local copy. LooqBaq runs fully offline once the model is on disk.

### 3. Pull LLMs via Ollama

```bash
ollama pull qwen3.5:9b
ollama pull mistral-nemo:12b
ollama pull gemma4:e4b
```

### 4. Run the transcription pipeline

Edit `video_path` in `main.py` to point to your recording, then:

```bash
python main.py
```

This produces `transcript.txt` with lines like:

```
[00.00s - 10.24s] Anushka: Just before we get started, do you mind if I have my note-taker on?
[12.00s - 14.00s] Maureen: Yeah, it's okay, that's no problem.
```

### 5. Extract action items

```bash
python text-inference.py
```

This chunks the transcript, runs it through each configured LLM, deduplicates results, and saves:
- `extracted_tasks_<model>.json` — tasks per model
- `analytics.json` — full benchmarking report

### 6. Launch the Streamlit app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Configuration

Key settings at the top of `text-inference.py`:

| Variable | Default | Description |
|---|---|---|
| `MODELS` | `["qwen3.5:9b", "mistral-nemo:12b", "gemma4:e4b"]` | Ollama models to benchmark |
| `CHUNK_SIZE_LINES` | `50` | Lines per transcript chunk |
| `OVERLAP_LINES` | `10` | Overlap between chunks to avoid cutting mid-thought |
| `TRANSCRIPT_PATH` | `transcript.txt` | Path to the transcript file |

---

## Output format

### transcript.txt

```
[00.00s - 28.00s] Maureen: So I'm the CTO at Payworks and we're exploring modernizing some legacy COBOL code.
[28.00s - 45.00s] Anushka: Our approach focuses heavily on documentation and knowledge transfer for long-term maintainability.
```

### extracted_tasks_\<model\>.json

```json
{
  "total_tasks": 8,
  "tasks": [
    {
      "speaker": "Anushka",
      "task_description": "Send case study write-up on the healthcare/insurance modernization project",
      "deadline": "Within 2 days",
      "priority": "High"
    }
  ]
}
```

### analytics.json

Contains per-model and per-chunk metrics: wall time, prompt/completion tokens, tasks found, deduplication count, and errors.

---

## Models tested

| Model | Unique Tasks | Speed | Notes |
|---|---|---|---|
| `mistral-nemo:12b` 🏆 | 8 | 12.2 tok/s | Best task recall |
| `qwen3.5:9b` | 7 | 14.5 tok/s | Fast, good quality |
| `gemma4:e4b` | 5 | 15.6 tok/s | Fastest, 1 chunk error |

Results from a 10:16 min customer discovery call (616s, 148 transcript lines).

---

## Hardware notes

LooqBaq is optimized for Apple Silicon. Pyannote runs on MPS (Metal GPU) and Whisper runs on CPU with `int8` quantization for a good speed/accuracy tradeoff on M1/M2/M3 Macs. To switch to CUDA, change `device="cpu"` to `device="cuda"` in `main.py`.

---

## Privacy

Everything runs locally. No audio, transcript, or task data is sent anywhere. The only network calls are optional model downloads via Hugging Face and Ollama (both of which can be pre-cached for fully air-gapped use).

---

## Built with

- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) — optimized Whisper inference
- [Pyannote Audio](https://github.com/pyannote/pyannote-audio) — speaker diarization
- [Ollama](https://ollama.com/) — local LLM inference
- [Streamlit](https://streamlit.io/) — web UI
- [Pydantic](https://docs.pydantic.dev/) — structured output validation

---

*LooqBaq — look back at every conversation, clearly.*