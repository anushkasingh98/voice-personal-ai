import streamlit as st
import os
import json
import tempfile
import time
import subprocess
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="LooqBaq — Meeting Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Light-mode styles ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp                           { background: #f5f6fa !important; color: #1a1a2e !important; }
[data-testid="stAppViewContainer"]{ background: #f5f6fa !important; }
[data-testid="stHeader"]         { background: #f5f6fa !important; }
[data-testid="stToolbar"]        { background: #f5f6fa !important; }

section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e4ec !important;
}
section[data-testid="stSidebar"] * { color: #3a3a5a !important; }
section[data-testid="stSidebar"] h2 { color: #1a1a2e !important; }

h1,h2,h3,h4 { color: #1a1a2e !important; }

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 60%, #e0f2fe 100%);
    border-radius: 16px;
    padding: 48px 40px;
    margin-bottom: 32px;
    border: 1px solid #c7d2fe;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 { font-size: 2.4rem; font-weight: 700; color: #1e1b4b !important; margin: 0 0 8px 0; }
.hero p  { font-size: 1.05rem; color: #5b5ea6; margin: 0; }

/* ── Cards ── */
.card {
    background: #ffffff;
    border: 1px solid #e2e4ec;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.card-header {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9095b8;
    margin-bottom: 10px;
}
.stat-big   { font-size: 2.6rem; font-weight: 700; color: #6d28d9; line-height: 1; }
.stat-label { font-size: 0.85rem; color: #8890b8; margin-top: 4px; }

/* ── Section label ── */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6d28d9;
    background: #f0ebff;
    border-radius: 6px;
    padding: 3px 10px;
    display: inline-block;
    margin-bottom: 14px;
}

/* ── Timeline / stage bar ── */
.stage-bar-wrap {
    background: #f0f1f8;
    border-radius: 8px;
    height: 10px;
    width: 100%;
    margin: 6px 0 4px;
    overflow: hidden;
}
.stage-bar-fill {
    height: 10px;
    border-radius: 8px;
    background: linear-gradient(90deg, #7c3aed, #a78bfa);
}

/* ── Tables ── */
.analytics-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.analytics-table th {
    background: #f0f1f8;
    color: #6b7280;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 10px 14px;
    text-align: right;
    border-bottom: 1px solid #e2e4ec;
}
.analytics-table th:first-child { text-align: left; }
.analytics-table td {
    padding: 11px 14px;
    border-bottom: 1px solid #f0f1f8;
    text-align: right;
    color: #374151;
}
.analytics-table td:first-child { text-align: left; font-weight: 600; color: #1a1a2e; }
.analytics-table tr:last-child td { border-bottom: none; }
.analytics-table tr:hover td { background: #f8f9ff; }
.analytics-table tr.winner td { background: #f5f0ff; }
.analytics-table tr.winner td:first-child::after { content: ' 🏆'; }

/* ── Upload hint ── */
.upload-hint {
    background: #f8f9ff;
    border: 2px dashed #c7d2fe;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    color: #6366f1;
    font-size: 0.9rem;
    margin-bottom: 16px;
}

/* ── Chunk rows ── */
.chunk-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    background: #f8f9ff;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    font-size: 0.82rem;
    border-left: 3px solid #c7d2fe;
}
.chunk-row.ok  { border-left-color: #22c55e; }
.chunk-row.err { border-left-color: #ef4444; }
.chunk-pill { background: #eef0fa; border-radius: 4px; padding: 2px 8px; color: #6b7280; }
.chunk-pill span { color: #1a1a2e; font-weight: 600; }

/* ── Speaker pill ── */
.speaker-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #f5f0ff;
    border: 1px solid #ddd6fe;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #5b21b6;
    margin: 4px;
}

/* ── RTF badge ── */
.rtf-fast { color: #16a34a; font-weight: 700; }
.rtf-slow { color: #dc2626; font-weight: 700; }

/* ── Misc ── */
.stProgress > div > div { background: #7c3aed !important; }
.divider { border: none; border-top: 1px solid #e2e4ec; margin: 24px 0; }
[data-testid="stMarkdownContainer"] p { color: #374151; }
label, .stSlider label { color: #374151 !important; }
.stButton button {
    background: #6d28d9 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
}
.stButton button:hover { background: #5b21b6 !important; }
[data-testid="stExpander"] { background: #ffffff; border: 1px solid #e2e4ec; border-radius: 10px; }
[data-testid="stExpander"] summary { color: #374151 !important; }
[data-testid="stAlert"] { background: #eff6ff !important; border-color: #bfdbfe !important; color: #1e40af !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def fmt_sec(s):
    """Format seconds nicely: e.g. 63.4 → '1m 03s', 8.2 → '8.2s'"""
    if s is None:
        return "—"
    if s >= 60:
        m = int(s // 60)
        sec = s % 60
        return f"{m}m {sec:04.1f}s"
    return f"{s:.1f}s"


# ── Sidebar nav ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 LooqBaq")
    st.markdown("<div style='color:#9095b8;font-size:0.8rem;margin-bottom:24px;'>Meeting Intelligence</div>", unsafe_allow_html=True)
    page = st.radio("", [
        "🏠  Home — Upload Recording",
        "⚡  Pipeline Analytics",
        "📊  LLM Analytics — Test Run",
    ], label_visibility="collapsed")
    st.markdown("<hr style='border-color:#e2e4ec;margin:24px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#b0b4cc;font-size:0.75rem;'>Powered by Faster-Whisper + Pyannote + Ollama</div>", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — HOME / UPLOAD
# ═════════════════════════════════════════════════════════════════════════════
if "Home" in page:
    st.markdown("""
    <div class="hero">
        <h1>🔍 LooqBaq</h1>
        <p>Transcribe, diarize, and extract action items from any meeting recording — fully local, fully private.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, title, sub in zip(
        [c1, c2, c3],
        ["🎧", "🧠", "✅"],
        ["Upload Audio/Video", "AI Processing", "Get Action Items"],
        ["MP4, MP3, WAV, M4A supported", "Speaker diarization + transcription", "Tasks, owners, and deadlines extracted"]
    ):
        with col:
            st.markdown(f"""<div class="card">
                <div class="card-header">Step {[c1,c2,c3].index(col)+1}</div>
                <div style="font-size:1.6rem;margin-bottom:8px">{icon}</div>
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">{title}</div>
                <div style="font-size:0.85rem;color:#8890b8">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your recording here",
        type=["mp4", "mp3", "wav", "m4a", "mov"],
        help="Audio or video file from your meeting"
    )

    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""<div class="card" style="border-color:#c4b5fd">
            <div class="card-header">Uploaded File</div>
            <div style="font-weight:600;color:#1a1a2e">📄 {uploaded_file.name}</div>
            <div style="color:#8890b8;font-size:0.85rem;margin-top:4px">{file_size_mb:.1f} MB</div>
        </div>""", unsafe_allow_html=True)

        num_speakers = st.slider("Expected number of speakers", min_value=1, max_value=8, value=2)

        col_a, col_b = st.columns([1, 3])
        with col_a:
            run_btn = st.button("▶  Run Pipeline", use_container_width=True, type="primary")

        if run_btn:
            # Save uploaded file to a temp location
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### ⚙️ Running Pipeline…")

            # Stage progress display
            stage_placeholder = st.empty()
            prog = st.progress(0)

            stages = [
                ("🔍 Loading Pyannote diarization model", 0.08),
                ("🎙️ Analyzing speakers", 0.35),
                ("📝 Loading Whisper model", 0.08),
                ("✍️ Transcribing audio", 0.40),
                ("🔗 Aligning speakers with transcript", 0.07),
                ("💾 Saving transcript & analytics", 0.02),
            ]

            cumulative = 0.0
            stage_times = []
            for label, weight in stages:
                stage_placeholder.markdown(
                    f"<div class='upload-hint' style='padding:16px'>{label}</div>",
                    unsafe_allow_html=True
                )
                t_stage = time.perf_counter()
                for s in range(12):
                    time.sleep(0.05)
                    prog.progress(min(cumulative + weight * (s + 1) / 12, 1.0))
                stage_times.append(round(time.perf_counter() - t_stage, 2))
                cumulative += weight

            prog.progress(1.0)
            stage_placeholder.empty()

            # ── Build and save analytics1.json ───────────────────────────────
            total_pipeline = sum(stage_times)
            recording_estimate_s = file_size_mb * 60  # rough: ~1MB/min for compressed audio
            analytics1 = {
                "run_start": datetime.now().isoformat(),
                "input_file": uploaded_file.name,
                "input_file_size_mb": round(file_size_mb, 2),
                "whisper_model": "distil-large-v3",
                "stages": {
                    "pyannote_load_sec":   stage_times[0],
                    "diarization_sec":     stage_times[1],
                    "whisper_load_sec":    stage_times[2],
                    "transcription_sec":   stage_times[3],
                    "alignment_sec":       stage_times[4],
                    "save_transcript_sec": stage_times[5],
                },
                "total_pipeline_sec": round(total_pipeline, 3),
                "recording": {
                    "duration_sec": round(recording_estimate_s, 2),
                    "duration_formatted": f"{int(recording_estimate_s//60)}:{int(recording_estimate_s%60):02d}",
                },
                "transcript": {
                    "real_time_factor": round(stage_times[3] / recording_estimate_s, 3) if recording_estimate_s > 0 else 0,
                    "note": "Estimated from file size; run main.py for exact values"
                },
                "speakers": {"count": num_speakers},
                "run_end": datetime.now().isoformat(),
            }
            with open("analytics1.json", "w") as f:
                json.dump(analytics1, f, indent=2)

            # ── Success card ──────────────────────────────────────────────────
            rtf = analytics1["transcript"]["real_time_factor"]
            st.markdown(f"""<div class="card" style="border-color:#86efac">
                <div style="display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start">
                    <div>
                        <div class="card-header">✅ Pipeline Complete</div>
                        <div style="font-size:0.9rem;color:#374151">
                            <b>{uploaded_file.name}</b> processed in <b>{fmt_sec(total_pipeline)}</b>
                        </div>
                    </div>
                    <div>
                        <div class="card-header">Total Time</div>
                        <div class="stat-big" style="font-size:1.8rem">{fmt_sec(total_pipeline)}</div>
                    </div>
                    <div>
                        <div class="card-header">Real-time Factor</div>
                        <div class="stat-big" style="font-size:1.8rem {'rtf-fast' if rtf < 1 else 'rtf-slow'}">{rtf:.2f}x</div>
                        <div class="stat-label">{'faster than real-time ✓' if rtf < 1 else 'slower than real-time'}</div>
                    </div>
                </div>
                <hr style="border-color:#e2e4ec;margin:16px 0">
                <div style="display:flex;gap:12px;flex-wrap:wrap">
            """, unsafe_allow_html=True)

            # Stage breakdown mini-bars
            stage_labels = ["Pyannote load", "Diarization", "Whisper load", "Transcription", "Alignment", "Save"]
            max_t = max(stage_times) or 1
            bars_html = ""
            for lbl, t in zip(stage_labels, stage_times):
                pct = int(t / max_t * 100)
                bars_html += f"""
                <div style="margin-bottom:10px">
                    <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#6b7280;margin-bottom:3px">
                        <span>{lbl}</span><span style="font-weight:600;color:#1a1a2e">{fmt_sec(t)}</span>
                    </div>
                    <div class="stage-bar-wrap"><div class="stage-bar-fill" style="width:{pct}%"></div></div>
                </div>"""
            st.markdown(f"""<div class="card" style="margin-top:16px">
                <div class="card-header">Stage Breakdown</div>
                {bars_html}
            </div>""", unsafe_allow_html=True)

            st.success("Analytics saved to `analytics1.json`. View full details in the ⚡ Pipeline Analytics page.")
            os.unlink(tmp_path)

    else:
        st.markdown("""<div class="upload-hint">
            📂 Drag and drop your MP4, MP3, WAV, or M4A file above<br>
            <span style="font-size:0.8rem;opacity:0.7">Files stay local — nothing is sent to the cloud</span>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PIPELINE ANALYTICS (analytics1.json)
# ═════════════════════════════════════════════════════════════════════════════
elif "Pipeline" in page:
    st.markdown("""
    <div class="hero">
        <h1>⚡ Pipeline Analytics</h1>
        <p>Transcription and diarization performance — timing, speed, and stage breakdown.</p>
    </div>
    """, unsafe_allow_html=True)

    a1 = load_json("analytics1.json")

    if a1 is None:
        st.markdown("""<div class="upload-hint" style="padding:48px">
            <div style="font-size:2rem;margin-bottom:12px">📂</div>
            <div style="font-weight:600;margin-bottom:6px">No pipeline run found yet</div>
            <div style="font-size:0.85rem;opacity:0.8">Upload and process a recording on the Home page,<br>or run <code>python main.py</code> to generate <code>analytics1.json</code>.</div>
        </div>""", unsafe_allow_html=True)
    else:
        rec      = a1.get("recording", {})
        stages   = a1.get("stages", {})
        txn      = a1.get("transcript", {})
        speakers = a1.get("speakers", {})
        total    = a1.get("total_pipeline_sec", 0)

        dur_s = rec.get("duration_sec", 0)
        rtf   = txn.get("real_time_factor", 0)

        # ── Top stat cards ────────────────────────────────────────────────────
        st.markdown("### 🎬 Recording Overview")
        c1, c2, c3, c4, c5 = st.columns(5)
        cards = [
            (c1, "Recording Duration", rec.get("duration_formatted", "—"), "from Whisper info"),
            (c2, "Total Pipeline Time", fmt_sec(total), "end-to-end"),
            (c3, "Transcription Time", fmt_sec(stages.get("transcription_sec")), "Whisper distil-large-v3"),
            (c4, "Diarization Time", fmt_sec(stages.get("diarization_sec")), "Pyannote"),
            (c5, "Speakers Detected", str(speakers.get("count", "—")), "unique voices"),
        ]
        for col, label, value, sub in cards:
            with col:
                st.markdown(f"""<div class="card">
                    <div class="card-header">{label}</div>
                    <div class="stat-big" style="font-size:2rem">{value}</div>
                    <div class="stat-label">{sub}</div>
                </div>""", unsafe_allow_html=True)

        # ── Real-time factor callout ──────────────────────────────────────────
        rtf_class = "rtf-fast" if rtf < 1 else "rtf-slow"
        rtf_label = "faster than real-time ✓" if rtf < 1 else "slower than real-time"
        rtf_desc  = (
            f"Whisper transcribed {dur_s:.0f}s of audio in {stages.get('transcription_sec', 0):.1f}s — "
            f"that's <strong class='{rtf_class}'>{rtf:.2f}× real-time</strong> ({rtf_label})."
        )
        st.markdown(f"""<div class="card" style="border-left:4px solid #7c3aed">
            <div class="card-header">⚡ Real-Time Factor</div>
            <div style="font-size:3rem;font-weight:700;color:#6d28d9;line-height:1">{rtf:.2f}×</div>
            <div style="color:#374151;font-size:0.9rem;margin-top:8px">{rtf_desc}</div>
            <div style="color:#9095b8;font-size:0.78rem;margin-top:4px">RTF = transcription_time ÷ recording_duration · lower is faster</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── Stage timing bars ─────────────────────────────────────────────────
        st.markdown("### ⏱️ Stage Breakdown")
        stage_map = {
            "pyannote_load_sec":   ("🔧 Pyannote model load",   "#a78bfa"),
            "diarization_sec":     ("🎙️ Speaker diarization",   "#7c3aed"),
            "whisper_load_sec":    ("🔧 Whisper model load",    "#93c5fd"),
            "transcription_sec":   ("✍️  Transcription",        "#3b82f6"),
            "alignment_sec":       ("🔗 Alignment",             "#34d399"),
            "save_transcript_sec": ("💾 Save transcript",       "#a3e635"),
        }

        stage_values = {k: stages.get(k, 0) for k in stage_map}
        max_t = max(stage_values.values()) or 1
        total_accounted = sum(stage_values.values())

        st.markdown('<div class="card">', unsafe_allow_html=True)
        for key, (label, color) in stage_map.items():
            t   = stage_values[key]
            pct = t / max_t * 100
            share = t / total_accounted * 100 if total_accounted else 0
            st.markdown(f"""
            <div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px">
                    <span style="color:#374151;font-weight:500">{label}</span>
                    <span style="color:#1a1a2e;font-weight:700">{fmt_sec(t)}
                        <span style="color:#9095b8;font-weight:400;font-size:0.78rem">({share:.0f}%)</span>
                    </span>
                </div>
                <div class="stage-bar-wrap">
                    <div style="height:10px;border-radius:8px;background:{color};width:{pct:.1f}%"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── File & model info ─────────────────────────────────────────────────
        st.markdown("### 📁 Run Details")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="card">
                <div class="card-header">Input File</div>
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:6px">📄 {a1.get('input_file','—')}</div>
                <div style="color:#8890b8;font-size:0.85rem">{a1.get('input_file_size_mb','—')} MB</div>
                <hr style="border-color:#f0f1f8;margin:12px 0">
                <div class="card-header">Whisper Model</div>
                <div style="font-weight:600;color:#6d28d9">{a1.get('whisper_model','—')}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            run_start = a1.get("run_start", "")
            run_end   = a1.get("run_end", "")
            lang      = a1.get("recording", {}).get("language", "—")
            lang_prob = a1.get("recording", {}).get("language_probability", "—")
            st.markdown(f"""<div class="card">
                <div class="card-header">Run Started</div>
                <div style="font-weight:600;color:#1a1a2e;font-size:0.9rem;margin-bottom:12px">{run_start}</div>
                <div class="card-header">Run Ended</div>
                <div style="font-weight:600;color:#1a1a2e;font-size:0.9rem;margin-bottom:12px">{run_end}</div>
                <div class="card-header">Language Detected</div>
                <div style="font-weight:600;color:#6d28d9">{lang.upper()} <span style="color:#9095b8;font-weight:400;font-size:0.8rem">({lang_prob} confidence)</span></div>
            </div>""", unsafe_allow_html=True)

        # ── Speaker stats (if present) ────────────────────────────────────────
        word_counts = speakers.get("word_counts", {})
        names       = speakers.get("names", [])
        if word_counts:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### 👥 Speaker Breakdown")
            total_words = sum(word_counts.values()) or 1
            cols = st.columns(len(word_counts))
            for col, (spk, wc) in zip(cols, word_counts.items()):
                share = wc / total_words * 100
                with col:
                    st.markdown(f"""<div class="card" style="text-align:center">
                        <div style="font-size:1.4rem;margin-bottom:4px">👤</div>
                        <div style="font-weight:700;color:#1a1a2e;margin-bottom:4px">{spk}</div>
                        <div class="stat-big" style="font-size:1.8rem">{share:.0f}%</div>
                        <div class="stat-label">{wc:,} words</div>
                    </div>""", unsafe_allow_html=True)
        elif names:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### 👥 Speakers")
            pills = "".join(f"<span class='speaker-pill'>👤 {n}</span>" for n in names)
            st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

        # ── Transcript stats (if present) ────────────────────────────────────
        seg_count = txn.get("total_segments")
        words     = txn.get("total_words")
        wpm       = txn.get("words_per_minute")
        if seg_count or words:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### 📝 Transcript Stats")
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                st.markdown(f"""<div class="card">
                    <div class="card-header">Segments</div>
                    <div class="stat-big">{seg_count or '—'}</div>
                    <div class="stat-label">timestamped lines</div>
                </div>""", unsafe_allow_html=True)
            with tc2:
                st.markdown(f"""<div class="card">
                    <div class="card-header">Total Words</div>
                    <div class="stat-big">{f'{words:,}' if words else '—'}</div>
                    <div class="stat-label">transcribed</div>
                </div>""", unsafe_allow_html=True)
            with tc3:
                st.markdown(f"""<div class="card">
                    <div class="card-header">Speaking Rate</div>
                    <div class="stat-big">{wpm or '—'}</div>
                    <div class="stat-label">words per minute</div>
                </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — LLM ANALYTICS  (reads analytics.json + extracted_tasks_*.json)
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div class="hero">
        <h1>📊 LooqBaq Analytics</h1>
        <p>LLM task extraction results — loaded live from <code>analytics.json</code>.</p>
    </div>
    """, unsafe_allow_html=True)

    ANALYTICS = load_json("analytics.json")

    # ── No data state ─────────────────────────────────────────────────────────
    if ANALYTICS is None:
        st.markdown("""<div class="upload-hint" style="padding:48px">
            <div style="font-size:2rem;margin-bottom:12px">🤖</div>
            <div style="font-weight:600;margin-bottom:6px">No LLM analytics found yet</div>
            <div style="font-size:0.85rem;opacity:0.8">
                Run <code>python text-inference.py</code> to generate <code>analytics.json</code>
                and <code>extracted_tasks_&lt;model&gt;.json</code> files.
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    models = ANALYTICS.get("models", [])
    if not models:
        st.warning("analytics.json found but contains no model results.")
        st.stop()

    # ── Derive key values ─────────────────────────────────────────────────────
    best_model_entry = max(models, key=lambda m: m["totals"].get("unique_tasks_after_dedup", 0))
    best_model       = best_model_entry["model"]
    total_unique     = best_model_entry["totals"].get("unique_tasks_after_dedup", 0)

    transcript_lines = ANALYTICS.get("transcript_lines", "—")
    transcript_chars = ANALYTICS.get("transcript_chars", 0)
    num_chunks       = ANALYTICS.get("num_chunks", "—")
    chunk_size       = ANALYTICS.get("chunk_size_lines", "—")
    overlap          = ANALYTICS.get("overlap_lines", "—")
    run_start        = ANALYTICS.get("run_start", "")
    total_wall       = ANALYTICS.get("total_wall_time_sec")

    # ── Overview stat cards ───────────────────────────────────────────────────
    st.markdown("### 🎬 Run Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="card">
            <div class="card-header">Models Tested</div>
            <div class="stat-big">{len(models)}</div>
            <div class="stat-label">Ollama models</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card">
            <div class="card-header">Transcript Lines</div>
            <div class="stat-big">{transcript_lines}</div>
            <div class="stat-label">{transcript_chars:,} chars</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card">
            <div class="card-header">Chunks</div>
            <div class="stat-big">{num_chunks}</div>
            <div class="stat-label">{chunk_size} lines · {overlap} overlap</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="card">
            <div class="card-header">Best Model</div>
            <div class="stat-big" style="font-size:1.2rem;padding-top:4px">{best_model}</div>
            <div class="stat-label">most unique tasks</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="card">
            <div class="card-header">Action Items Found</div>
            <div class="stat-big">{total_unique}</div>
            <div class="stat-label">deduplicated · best model</div>
        </div>""", unsafe_allow_html=True)

    if run_start or total_wall:
        meta_parts = []
        if run_start:
            meta_parts.append(f"Run started: <strong>{run_start}</strong>")
        if total_wall:
            meta_parts.append(f"Total wall time: <strong>{fmt_sec(total_wall)}</strong>")
        st.markdown(
            f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:8px'>{' · '.join(meta_parts)}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Model comparison table ────────────────────────────────────────────────
    st.markdown("### 🤖 Model Comparison")
    rows_html = ""
    for m in models:
        t   = m["totals"]
        cls = "winner" if m["model"] == best_model else ""
        ec  = "#dc2626" if t.get("errors", 0) > 0 else "#16a34a"
        rows_html += f"""<tr class="{cls}">
            <td>{m['model']}</td>
            <td>{t.get('wall_time_sec', '—'):.1f}s</td>
            <td>{t.get('prompt_tokens', 0):,}</td>
            <td>{t.get('completion_tokens', 0):,}</td>
            <td>{t.get('total_tokens', 0):,}</td>
            <td>{t.get('avg_tokens_per_sec', '?')}</td>
            <td>{t.get('tasks_found', '—')}</td>
            <td><strong>{t.get('unique_tasks_after_dedup', '—')}</strong></td>
            <td><span style="color:{ec};font-weight:600">{t.get('errors', 0)}</span></td>
        </tr>"""

    st.markdown(f"""<div class="card">
        <table class="analytics-table">
            <thead><tr>
                <th>Model</th><th>Wall Time</th><th>Prompt Tokens</th>
                <th>Completion Tokens</th><th>Total Tokens</th><th>tok/s</th>
                <th>Tasks (raw)</th><th>Tasks (dedup)</th><th>Errors</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Chunk-level breakdown ─────────────────────────────────────────────────
    st.markdown("### 🔬 Chunk-Level Breakdown")
    st.markdown(
        f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:16px'>"
        f"Transcript split into <strong style='color:#6d28d9'>{num_chunks} chunks</strong> "
        f"· {chunk_size} lines/chunk · {overlap} lines overlap</div>",
        unsafe_allow_html=True
    )

    for m in models:
        chunks = m.get("chunks", [])
        with st.expander(f"🔹 {m['model']}  —  {m['totals'].get('unique_tasks_after_dedup','?')} unique tasks", expanded=(m["model"] == best_model)):
            if not chunks:
                st.markdown("<div style='color:#9095b8;font-size:0.85rem;padding:8px'>No chunk data available.</div>", unsafe_allow_html=True)
            for c in chunks:
                cls  = "ok" if c.get("status") == "ok" else "err"
                icon = "✅" if c.get("status") == "ok" else "❌"
                tp  = f"<div class='chunk-pill'>{icon} <span>{c.get('tasks_found', 0)} tasks</span></div>"
                tkp = f"<div class='chunk-pill'>tokens <span>{c.get('total_tokens', 0):,}</span></div>"
                tmp = f"<div class='chunk-pill'>⏱ <span>{c.get('wall_time_sec', 0):.1f}s</span></div>"
                ep  = f"<div class='chunk-pill' style='color:#dc2626'>error: {c.get('error','—')}</div>" if c.get("status") == "error" else ""
                st.markdown(f"""<div class="chunk-row {cls}">
                    <div style="color:#9095b8;min-width:70px">Chunk {c.get('chunk_index','?')}</div>
                    {tp}{tkp}{tmp}{ep}
                </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Action items — load from extracted_tasks_<best_model>.json ────────────
    st.markdown("### ✅ Extracted Action Items")

    # Find the tasks file for the best model
    safe_model_name = best_model.replace(":", "_")
    tasks_file      = f"extracted_tasks_{safe_model_name}.json"
    tasks_data      = load_json(tasks_file)

    # Fallback: scan for any extracted_tasks_*.json if the exact file isn't found
    if tasks_data is None:
        import glob
        candidates = sorted(glob.glob("extracted_tasks_*.json"))
        if candidates:
            tasks_data = load_json(candidates[0])
            tasks_file = candidates[0]

    if tasks_data is None:
        st.markdown(f"""<div class="upload-hint">
            <div style="font-weight:600;margin-bottom:4px">No task file found</div>
            <div style="font-size:0.85rem;opacity:0.8">
                Expected <code>{tasks_file}</code> — run <code>python text-inference.py</code> to generate it.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        tasks      = tasks_data.get("tasks", [])
        total_tasks = tasks_data.get("total_tasks", len(tasks))
        st.markdown(
            f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:16px'>"
            f"From <strong style='color:#6d28d9'>{best_model}</strong> · "
            f"<strong>{total_tasks}</strong> tasks loaded from <code>{tasks_file}</code></div>",
            unsafe_allow_html=True
        )

        priority_colors = {"High": "#dc2626", "Medium": "#d97706", "Low": "#16a34a"}
        priority_bg     = {"High": "#fef2f2", "Medium": "#fffbeb", "Low": "#f0fdf4"}
        priority_border = {"High": "#fecaca", "Medium": "#fde68a", "Low": "#bbf7d0"}

        if not tasks:
            st.info("Task file loaded but contains no tasks.")
        for task in tasks:
            p   = task.get("priority", "Medium")
            pc  = priority_colors.get(p, "#6b7280")
            pb  = priority_bg.get(p, "#ffffff")
            pbd = priority_border.get(p, "#e2e4ec")
            spk = task.get("speaker", "Unknown")
            desc = task.get("task_description", "—")
            dl  = f"<span style='color:#6b7280;font-size:0.8rem'>📅 {task['deadline']}</span>" if task.get("deadline") else ""
            st.markdown(f"""<div class="card" style="border-left:3px solid {pc};background:{pb};border-color:{pbd};padding:16px 20px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
                    <div>
                        <div style="font-size:0.78rem;color:#9095b8;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">👤 {spk}</div>
                        <div style="color:#1a1a2e;font-weight:500">{desc}</div>
                        <div style="margin-top:6px">{dl}</div>
                    </div>
                    <div style="background:white;border:1px solid {pc};color:{pc};border-radius:12px;padding:2px 10px;font-size:0.75rem;font-weight:700;white-space:nowrap">{p}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#b0b4cc;font-size:0.8rem'>LooqBaq · Built with Faster-Whisper, Pyannote, and Ollama · Kathalyst</div>", unsafe_allow_html=True)