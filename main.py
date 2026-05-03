# pip install faster-whisper
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import torch
import os

os.environ["HF_HUB_OFFLINE"] = "1"        # Forces Hugging Face to stay offline
os.environ["PYANNOTE_METRICS_ENABLED"] = "0" # Disables telemetry

print("--- Setting up ---\n\n")
# Point to the local folder you just created
local_model_path = "/Users/anushkasingh/Desktop/Code/Sundai/voice_may3_26/local_pyannote_model/config.yaml"

# Load from disk - no internet required!
# pipeline = Pipeline.from_pretrained(local_model_path, token=HF_TOKEN)
pipeline = Pipeline.from_pretrained(local_model_path)

# Move to M1 Mac GPU (MPS)

pipeline.to(torch.device("mps"))

video_path = "/Users/anushkasingh/Desktop/Code/Sundai/voice_may3_26/voice-personal-ai/test-recordings/Maureen - Jan 19 2026.mp4"


# 1. Initialize Pyannote Diarization (Optimized for Mac CPU/MPS)
# print("--- Initializing Speaker Diarization ---")
# diarization_pipeline = Pipeline.from_pretrained(
#     "pyannote/speaker-diarization-3.1",
#     use_auth_token=HF_TOKEN
# )
# # Use MPS (Metal) for Pyannote if available, otherwise CPU
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
# diarization_pipeline.to(device)

# 2. Run Diarization
print("--- Analyzing speakers ---")
# pyannote handles video via ffmpeg internally
diarization = pipeline(video_path)

# 3. Initialize Faster-Whisper
print("--- Initializing Transcription ---")
whisper_model = WhisperModel("distil-large-v3", device="cpu", compute_type="int8")
segments, _ = whisper_model.transcribe(video_path, beam_size=5)

# 4. Alignment Logic
print("\n--- Final Transcript ---\n")

segments = list(segments) # Buffer segments to align
print(segments)

for segment in segments:
    # Find the speaker who was talking during this whisper segment's time
    # We look for the speaker with the most overlap in this time range
    speaker = "UNKNOWN"
    max_overlap = 0
    
    # Check Pyannote's timeline for this specific segment's start/end
    for turn, _, speaker_label in diarization.speaker_diarization.itertracks(yield_label=True):
        # Calculate overlap between whisper segment and pyannote turn
        overlap = min(segment.end, turn.end) - max(segment.start, turn.start)
        if overlap > max_overlap:
            max_overlap = overlap
            speaker = speaker_label
            
    print(f"[{segment.start:05.2f}s - {segment.end:05.2f}s] {speaker}: {segment.text.strip()}")

# ... (Keep your existing initialization and processing code) ...

# 4. Alignment and Speaker Naming Logic
print("\n--- Processing Transcript ---\n")

segments = list(segments)
full_transcript_data = []
unique_speakers = set()

# Process all segments and identify unique speakers
for segment in segments:
    speaker = "UNKNOWN"
    max_overlap = 0
    for turn, _, speaker_label in diarization.speaker_diarization.itertracks(yield_label=True):
        overlap = min(segment.end, turn.end) - max(segment.start, turn.start)
        if overlap > max_overlap:
            max_overlap = overlap
            speaker = speaker_label
    
    full_transcript_data.append((segment.start, segment.end, speaker, segment.text.strip()))
    unique_speakers.add(speaker)

# 5. Display first 3 minutes (180 seconds)
print("--- Preview (First 3 Minutes) ---")
for start, end, speaker, text in full_transcript_data:
    if start > 180:
        break
    print(f"[{start:05.2f}s - {end:05.2f}s] {speaker}: {text}")

# 6. User Input for Speaker Names
print("\n--- Name the Speakers ---")
speaker_map = {}
for speaker_id in sorted(list(unique_speakers)):
    name = input(f"Enter name for {speaker_id}: ")
    speaker_map[speaker_id] = name

# 7. Save to Text File
output_file = "transcript.txt"
with open(output_file, "w") as f:
    for start, end, speaker_id, text in full_transcript_data:
        real_name = speaker_map.get(speaker_id, speaker_id)
        line = f"[{start:05.2f}s - {end:05.2f}s] {real_name}: {text}\n"
        f.write(line)

print(f"\n--- Transcript saved to {output_file} ---")