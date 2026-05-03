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

for segment in segments:
    # Find the speaker who was talking during this whisper segment's time
    # We look for the speaker with the most overlap in this time range
    speaker = "UNKNOWN"
    max_overlap = 0
    
    # Check Pyannote's timeline for this specific segment's start/end
    for turn, _, speaker_label in diarization.itertracks(yield_label=True):
        # Calculate overlap between whisper segment and pyannote turn
        overlap = min(segment.end, turn.end) - max(segment.start, turn.start)
        if overlap > max_overlap:
            max_overlap = overlap
            speaker = speaker_label
            
    print(f"[{segment.start:05.2f}s - {segment.end:05.2f}s] {speaker}: {segment.text.strip()}")

# # Run as usual
# diarization = pipeline("your_video.mp4")

# # Options: "tiny", "base", "small", "medium", "large-v3", "distil-large-v3"
# model_size = "large-v3-turbo"
# device_ = "cpu"
# compute_type_ = "int8"  # Use "int8" for older hardware, "float16" for newer GPUs

# # Run on GPU with FP16 precision, or "cpu" with "int8" for older hardware
# model = WhisperModel(model_size, device=device_, compute_type=compute_type_)

# video_path = "/Users/anushkasingh/Desktop/Code/Sundai/voice_may3_26/voice-personal-ai/test-recordings/Maureen - Jan 19 2026.mp4"

# if not os.path.exists(video_path):
#     print(f"Error: Could not find {video_path}")
# else:
#     print(f"--- Transcribing: {video_path} ---")
    
#     # transcribe() handles .mp4, .mkv, .mov etc. automatically via ffmpeg
#     segments, info = model.transcribe(
#         video_path, 
#         beam_size=5,
#         vad_filter=True, # Recommended: Removes silent gaps to prevent hallucinations
#         word_timestamps=True # Optional: gives you timing for every single word
#     )

#     print(f"Detected Language: {info.language} (Probability: {info.language_probability:.2f})")

#     # 3. Process the output
#     for segment in segments:
#         print(f"[{segment.start:>6.2f}s -> {segment.end:>6.2f}s] {segment.text}")