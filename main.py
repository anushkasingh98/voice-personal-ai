# pip install faster-whisper pyannote.audio torch
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import torch
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"         # Forces Hugging Face to stay offline
os.environ["PYANNOTE_METRICS_ENABLED"] = "0" # Disables telemetry

# ── Config ────────────────────────────────────────────────────────────────────
LOCAL_MODEL_PATH = "./local_pyannote_model/config.yaml"
WHISPER_MODEL    = "distil-large-v3"
ANALYTICS_PATH   = "analytics1.json"


def format_duration(seconds: float) -> str:
    """Convert seconds to mm:ss string."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def get_file_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def run_pipeline(video_path: str, output_transcript: str = "transcript.txt") -> dict:
    """
    Full diarization + transcription pipeline.
    Returns an analytics dict that is also written to analytics1.json.
    """
    run_start_wall  = time.perf_counter()
    run_start_dt    = datetime.now().isoformat()
    file_size_mb    = get_file_size_mb(video_path)

    analytics = {
        "run_start": run_start_dt,
        "input_file": os.path.basename(video_path),
        "input_file_size_mb": round(file_size_mb, 2),
        "whisper_model": WHISPER_MODEL,
        "stages": {},
        "recording": {},
        "transcript": {},
        "speakers": {},
        "output_file": output_transcript,
    }

    # ── Stage 1: Load Pyannote ────────────────────────────────────────────────
    print("\n--- Setting up Pyannote ---")
    t0 = time.perf_counter()
    pipeline = Pipeline.from_pretrained(LOCAL_MODEL_PATH)
    pipeline.to(torch.device("mps" if torch.backends.mps.is_available() else "cpu"))
    analytics["stages"]["pyannote_load_sec"] = round(time.perf_counter() - t0, 3)
    print(f"    Pyannote loaded in {analytics['stages']['pyannote_load_sec']}s")

    # ── Stage 2: Speaker diarization ─────────────────────────────────────────
    print("--- Analyzing speakers ---")
    t0 = time.perf_counter()
    diarization = pipeline(video_path)
    analytics["stages"]["diarization_sec"] = round(time.perf_counter() - t0, 3)
    print(f"    Diarization done in {analytics['stages']['diarization_sec']}s")

    # ── Stage 3: Load Whisper ─────────────────────────────────────────────────
    print("--- Initializing Whisper ---")
    t0 = time.perf_counter()
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    analytics["stages"]["whisper_load_sec"] = round(time.perf_counter() - t0, 3)
    print(f"    Whisper loaded in {analytics['stages']['whisper_load_sec']}s")

    # ── Stage 4: Transcription ────────────────────────────────────────────────
    print("--- Transcribing ---")
    t0 = time.perf_counter()
    segments_gen, info = whisper_model.transcribe(video_path, beam_size=5)
    segments = list(segments_gen)   # buffer all segments
    analytics["stages"]["transcription_sec"] = round(time.perf_counter() - t0, 3)
    print(f"    Transcription done in {analytics['stages']['transcription_sec']}s")

    # Derive recording duration from Whisper's info object
    recording_duration_s = float(info.duration) if hasattr(info, "duration") else (
        segments[-1].end if segments else 0.0
    )
    analytics["recording"] = {
        "duration_sec": round(recording_duration_s, 2),
        "duration_formatted": format_duration(recording_duration_s),
        "language": getattr(info, "language", "unknown"),
        "language_probability": round(getattr(info, "language_probability", 0.0), 3),
    }

    # ── Stage 5: Alignment ────────────────────────────────────────────────────
    print("--- Aligning transcript with speakers ---")
    t0 = time.perf_counter()

    full_transcript_data = []
    unique_speakers = set()

    for segment in segments:
        speaker = "UNKNOWN"
        max_overlap = 0.0
        for turn, _, speaker_label in diarization.itertracks(yield_label=True):
            overlap = min(segment.end, turn.end) - max(segment.start, turn.start)
            if overlap > max_overlap:
                max_overlap = overlap
                speaker = speaker_label
        full_transcript_data.append((segment.start, segment.end, speaker, segment.text.strip()))
        unique_speakers.add(speaker)

    analytics["stages"]["alignment_sec"] = round(time.perf_counter() - t0, 3)
    print(f"    Alignment done in {analytics['stages']['alignment_sec']}s")

    # ── Speaker naming (interactive) ──────────────────────────────────────────
    print("\n--- Preview (First 3 Minutes) ---")
    for start, end, speaker, text in full_transcript_data:
        if start > 180:
            break
        print(f"[{start:05.2f}s - {end:05.2f}s] {speaker}: {text}")

    print("\n--- Name the Speakers ---")
    speaker_map = {}
    for speaker_id in sorted(unique_speakers):
        name = input(f"Enter name for {speaker_id} (or press Enter to keep '{speaker_id}'): ").strip()
        speaker_map[speaker_id] = name if name else speaker_id

    # ── Stage 6: Save transcript ──────────────────────────────────────────────
    t0 = time.perf_counter()
    with open(output_transcript, "w") as f:
        for start, end, speaker_id, text in full_transcript_data:
            real_name = speaker_map.get(speaker_id, speaker_id)
            f.write(f"[{start:05.2f}s - {end:05.2f}s] {real_name}: {text}\n")
    analytics["stages"]["save_transcript_sec"] = round(time.perf_counter() - t0, 3)

    # ── Transcript stats ──────────────────────────────────────────────────────
    total_words = sum(len(text.split()) for *_, text in full_transcript_data)
    analytics["transcript"] = {
        "output_file": output_transcript,
        "total_segments": len(full_transcript_data),
        "total_words": total_words,
        "words_per_minute": round(total_words / (recording_duration_s / 60), 1) if recording_duration_s > 0 else 0,
        "real_time_factor": round(analytics["stages"]["transcription_sec"] / recording_duration_s, 3) if recording_duration_s > 0 else 0,
    }

    # ── Speaker stats ─────────────────────────────────────────────────────────
    speaker_word_counts = {}
    speaker_segment_counts = {}
    for _, _, speaker_id, text in full_transcript_data:
        real_name = speaker_map.get(speaker_id, speaker_id)
        speaker_word_counts[real_name]    = speaker_word_counts.get(real_name, 0) + len(text.split())
        speaker_segment_counts[real_name] = speaker_segment_counts.get(real_name, 0) + 1

    analytics["speakers"] = {
        "count": len(unique_speakers),
        "names": list(speaker_map.values()),
        "word_counts": speaker_word_counts,
        "segment_counts": speaker_segment_counts,
    }

    # ── Totals ────────────────────────────────────────────────────────────────
    total_pipeline_sec = round(time.perf_counter() - run_start_wall, 3)
    analytics["total_pipeline_sec"] = total_pipeline_sec
    analytics["run_end"] = datetime.now().isoformat()
    analytics["speed_summary"] = {
        "recording_duration_sec": round(recording_duration_s, 2),
        "total_pipeline_sec": total_pipeline_sec,
        "diarization_sec": analytics["stages"]["diarization_sec"],
        "transcription_sec": analytics["stages"]["transcription_sec"],
        "real_time_factor": analytics["transcript"]["real_time_factor"],
        "note": "Real-time factor < 1 means transcription was faster than the recording",
    }

    # ── Save analytics ────────────────────────────────────────────────────────
    with open(ANALYTICS_PATH, "w") as f:
        json.dump(analytics, f, indent=2)

    print(f"\n--- Transcript saved to {output_transcript} ---")
    print(f"--- Pipeline analytics saved to {ANALYTICS_PATH} ---")
    print(f"\nTotal pipeline time : {total_pipeline_sec}s")
    print(f"Recording duration  : {format_duration(recording_duration_s)}")
    print(f"Real-time factor    : {analytics['transcript']['real_time_factor']}x")

    return analytics


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LooqBaq — transcribe and diarize a meeting recording"
    )
    parser.add_argument(
        "recording",
        nargs="?",
        help="Path to the audio/video file to process. If omitted, you will be prompted."
    )
    parser.add_argument(
        "--output", "-o",
        default="transcript.txt",
        help="Output transcript file path (default: transcript.txt)"
    )
    args = parser.parse_args()

    # Allow interactive path entry if not passed as CLI arg
    if args.recording:
        video_path = args.recording
    else:
        video_path = input("Enter path to your recording file: ").strip().strip("'\"")

    if not os.path.exists(video_path):
        print(f"Error: file not found — {video_path}")
        exit(1)

    run_pipeline(video_path, output_transcript=args.output)