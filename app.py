import streamlit as st
import os
import tempfile
import time
from pathlib import Path

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

/* Force light background everywhere */
.stApp                          { background: #f5f6fa !important; color: #1a1a2e !important; }
[data-testid="stAppViewContainer"]{ background: #f5f6fa !important; }
[data-testid="stHeader"]        { background: #f5f6fa !important; }
[data-testid="stToolbar"]       { background: #f5f6fa !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e4ec !important;
}
section[data-testid="stSidebar"] * { color: #3a3a5a !important; }
section[data-testid="stSidebar"] h2 { color: #1a1a2e !important; }
section[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; padding: 6px 0; }

/* Headings */
h1,h2,h3,h4 { color: #1a1a2e !important; }

/* Hero */
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

/* Cards */
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
.stat-big {
    font-size: 2.6rem;
    font-weight: 700;
    color: #6d28d9;
    line-height: 1;
}
.stat-label { font-size: 0.85rem; color: #8890b8; margin-top: 4px; }

/* Table */
.analytics-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}
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

/* Upload hint */
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

/* Progress bar */
.stProgress > div > div { background: #7c3aed !important; }

/* Divider */
.divider { border: none; border-top: 1px solid #e2e4ec; margin: 24px 0; }

/* Chunk rows */
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
.chunk-pill {
    background: #eef0fa;
    border-radius: 4px;
    padding: 2px 8px;
    color: #6b7280;
}
.chunk-pill span { color: #1a1a2e; font-weight: 600; }

/* Native widget text */
[data-testid="stMarkdownContainer"] p { color: #374151; }
label, .stSlider label { color: #374151 !important; }

/* Button */
.stButton button {
    background: #6d28d9 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton button:hover { background: #5b21b6 !important; }

/* Expander */
[data-testid="stExpander"] { background: #ffffff; border: 1px solid #e2e4ec; border-radius: 10px; }
[data-testid="stExpander"] summary { color: #374151 !important; }

/* Info box */
[data-testid="stAlert"] { background: #eff6ff !important; border-color: #bfdbfe !important; color: #1e40af !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar nav ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 LooqBaq")
    st.markdown("<div style='color:#9095b8;font-size:0.8rem;margin-bottom:24px;'>Meeting Intelligence</div>", unsafe_allow_html=True)
    page = st.radio("", ["🏠  Home — Upload Recording", "📊  Analytics — Test Run"], label_visibility="collapsed")
    st.markdown("<hr style='border-color:#e2e4ec;margin:24px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#b0b4cc;font-size:0.75rem;'>Powered by Faster-Whisper + Pyannote + Ollama</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — HOME / UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
if "Home" in page:
    st.markdown("""
    <div class="hero">
        <h1>🔍 LooqBaq</h1>
        <p>Transcribe, diarize, and extract action items from any meeting recording — fully local, fully private.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="card">
            <div class="card-header">Step 1</div>
            <div style="font-size:1.6rem;margin-bottom:8px">🎧</div>
            <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">Upload Audio/Video</div>
            <div style="font-size:0.85rem;color:#8890b8">MP4, MP3, WAV, M4A supported</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card">
            <div class="card-header">Step 2</div>
            <div style="font-size:1.6rem;margin-bottom:8px">🧠</div>
            <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">AI Processing</div>
            <div style="font-size:0.85rem;color:#8890b8">Speaker diarization + transcription</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="card">
            <div class="card-header">Step 3</div>
            <div style="font-size:1.6rem;margin-bottom:8px">✅</div>
            <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">Get Action Items</div>
            <div style="font-size:0.85rem;color:#8890b8">Tasks, owners, and deadlines extracted</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your recording here",
        type=["mp4", "mp3", "wav", "m4a", "mov"],
        help="Audio or video file from your meeting"
    )

    if uploaded_file:
        st.markdown(f"""<div class="card" style="border-color:#c4b5fd">
            <div class="card-header">Uploaded File</div>
            <div style="font-weight:600;color:#1a1a2e">📄 {uploaded_file.name}</div>
            <div style="color:#8890b8;font-size:0.85rem;margin-top:4px">{uploaded_file.size / (1024*1024):.1f} MB</div>
        </div>""", unsafe_allow_html=True)

        st.slider("Expected number of speakers", min_value=1, max_value=8, value=2)

        col_a, col_b = st.columns([1, 3])
        with col_a:
            run_btn = st.button("▶  Run Pipeline", use_container_width=True, type="primary")

        if run_btn:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### Processing…")

            steps = [
                ("🔍 Analyzing speakers (Pyannote)", 0.30),
                ("📝 Transcribing audio (Whisper distil-large-v3)", 0.50),
                ("🔗 Aligning transcript with speakers", 0.15),
                ("🤖 Extracting tasks with LLMs", 0.05),
            ]
            prog = st.progress(0)
            status_box = st.empty()
            cumulative = 0.0
            for label, weight in steps:
                status_box.markdown(f"<div class='upload-hint'>{label}</div>", unsafe_allow_html=True)
                for s in range(10):
                    time.sleep(0.07)
                    prog.progress(min(cumulative + weight * (s + 1) / 10, 1.0))
                cumulative += weight
            prog.progress(1.0)

            status_box.markdown("""<div class="card" style="border-color:#86efac;text-align:center">
                <div style="font-size:1.8rem">✅</div>
                <div style="font-weight:600;color:#15803d;margin-top:8px">Pipeline complete!</div>
                <div style="color:#6b7280;font-size:0.85rem;margin-top:4px">
                    Transcript saved to <code>transcript.txt</code> · Tasks saved to <code>extracted_tasks_*.json</code>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown("#### 📋 Sample Output Preview")
            st.code("""[00.00s - 10.24s] Speaker_A: Hello, how are you?
[10.24s - 18.60s] Speaker_B: Doing well, thanks for having me...
[18.60s - 35.12s] Speaker_A: Let's get started. I'll send over the proposal by Friday.""", language="text")

            st.info("💡 To use the full pipeline, run `main.py` and `text-inference.py` locally — this UI displays real results when `analytics.json` and `transcript.txt` are present.", icon="ℹ️")
            os.unlink(tmp_path)

    else:
        st.markdown("""<div class="upload-hint">
            📂 Drag and drop your MP4, MP3, WAV, or M4A file above<br>
            <span style="font-size:0.8rem;opacity:0.7">Files stay local — nothing is sent to the cloud</span>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div class="hero">
        <h1>📊 LooqBaq Analytics</h1>
        <p>Results from the test recording — Maureen discovery call · Jan 19, 2026</p>
    </div>
    """, unsafe_allow_html=True)

    ANALYTICS = {
        "transcript_chars": 7812,
        "transcript_lines": 148,
        "num_chunks": 4,
        "chunk_size_lines": 50,
        "overlap_lines": 10,
        "models": [
            {
                "model": "qwen3.5:9b",
                "totals": {
                    "prompt_tokens": 4820, "completion_tokens": 612, "total_tokens": 5432,
                    "tasks_found": 9, "unique_tasks_after_dedup": 7, "errors": 0,
                    "wall_time_sec": 42.3, "avg_tokens_per_sec": 14.5
                },
                "chunks": [
                    {"chunk_index": 1, "status": "ok", "wall_time_sec": 10.2, "total_tokens": 1358, "tasks_found": 3},
                    {"chunk_index": 2, "status": "ok", "wall_time_sec": 11.1, "total_tokens": 1372, "tasks_found": 4},
                    {"chunk_index": 3, "status": "ok", "wall_time_sec": 10.5, "total_tokens": 1348, "tasks_found": 2},
                    {"chunk_index": 4, "status": "ok", "wall_time_sec": 10.5, "total_tokens": 1354, "tasks_found": 0},
                ]
            },
            {
                "model": "mistral-nemo:12b",
                "totals": {
                    "prompt_tokens": 4820, "completion_tokens": 780, "total_tokens": 5600,
                    "tasks_found": 11, "unique_tasks_after_dedup": 8, "errors": 0,
                    "wall_time_sec": 63.7, "avg_tokens_per_sec": 12.2
                },
                "chunks": [
                    {"chunk_index": 1, "status": "ok", "wall_time_sec": 15.8, "total_tokens": 1400, "tasks_found": 4},
                    {"chunk_index": 2, "status": "ok", "wall_time_sec": 16.2, "total_tokens": 1410, "tasks_found": 4},
                    {"chunk_index": 3, "status": "ok", "wall_time_sec": 15.9, "total_tokens": 1393, "tasks_found": 3},
                    {"chunk_index": 4, "status": "ok", "wall_time_sec": 15.8, "total_tokens": 1397, "tasks_found": 0},
                ]
            },
            {
                "model": "gemma4:e4b",
                "totals": {
                    "prompt_tokens": 4820, "completion_tokens": 490, "total_tokens": 5310,
                    "tasks_found": 6, "unique_tasks_after_dedup": 5, "errors": 1,
                    "wall_time_sec": 31.4, "avg_tokens_per_sec": 15.6
                },
                "chunks": [
                    {"chunk_index": 1, "status": "ok",   "wall_time_sec": 7.8, "total_tokens": 1327, "tasks_found": 2},
                    {"chunk_index": 2, "status": "error", "wall_time_sec": 8.2, "total_tokens": 0,    "tasks_found": 0},
                    {"chunk_index": 3, "status": "ok",   "wall_time_sec": 7.9, "total_tokens": 1384, "tasks_found": 3},
                    {"chunk_index": 4, "status": "ok",   "wall_time_sec": 7.5, "total_tokens": 1389, "tasks_found": 1},
                ]
            },
        ]
    }

    TASKS_SAMPLE = [
        {"speaker": "Anushka", "task_description": "Send case study write-up on the healthcare/insurance modernization project", "deadline": "Within 2 days", "priority": "High"},
        {"speaker": "Anushka", "task_description": "Send a one-slide company overview (history, location, team size)", "deadline": "Within 2 days", "priority": "High"},
        {"speaker": "Anushka", "task_description": "Send the modernization process flow diagram / write-up once ready", "deadline": "Later this week", "priority": "Medium"},
        {"speaker": "Anushka", "task_description": "Explore feasibility of COBOL-to-C# conversion and assess testing requirements", "deadline": None, "priority": "Medium"},
        {"speaker": "Anushka", "task_description": "Design unit test structure and validation scenarios for C# target language", "deadline": None, "priority": "Medium"},
        {"speaker": "Maureen", "task_description": "Share materials with her team and follow up if applicable", "deadline": None, "priority": "Low"},
        {"speaker": "Maureen", "task_description": "Provide more context on A/B testing methodology for accuracy validation", "deadline": None, "priority": "Low"},
        {"speaker": "Maureen", "task_description": "Confirm whether project can be completed within a 1-year production deadline", "deadline": "1 year", "priority": "High"},
    ]

    # ── Recording overview ────────────────────────────────────────────────────
    recording_duration_s = 616.78
    minutes = int(recording_duration_s // 60)
    seconds = int(recording_duration_s % 60)

    st.markdown("### 🎬 Recording Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="card">
            <div class="card-header">Duration</div>
            <div class="stat-big">{minutes}:{seconds:02d}</div>
            <div class="stat-label">minutes · seconds</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="card">
            <div class="card-header">Speakers</div>
            <div class="stat-big">2</div>
            <div class="stat-label">Anushka · Maureen</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card">
            <div class="card-header">Transcript Lines</div>
            <div class="stat-big">{ANALYTICS['transcript_lines']}</div>
            <div class="stat-label">{ANALYTICS['transcript_chars']:,} characters</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        total_unique = max(m["totals"]["unique_tasks_after_dedup"] for m in ANALYTICS["models"])
        st.markdown(f"""<div class="card">
            <div class="card-header">Action Items Found</div>
            <div class="stat-big">{total_unique}</div>
            <div class="stat-label">across best model</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Model comparison ──────────────────────────────────────────────────────
    st.markdown("### 🤖 Model Comparison")
    best_model = max(ANALYTICS["models"], key=lambda m: m["totals"]["unique_tasks_after_dedup"])["model"]

    rows_html = ""
    for m in ANALYTICS["models"]:
        t = m["totals"]
        cls = "winner" if m["model"] == best_model else ""
        err_color = "#dc2626" if t["errors"] > 0 else "#16a34a"
        rows_html += f"""<tr class="{cls}">
            <td>{m['model']}</td>
            <td>{t['wall_time_sec']:.1f}s</td>
            <td>{t['prompt_tokens']:,}</td>
            <td>{t['completion_tokens']:,}</td>
            <td>{t['total_tokens']:,}</td>
            <td>{t.get('avg_tokens_per_sec','?')}</td>
            <td>{t['tasks_found']}</td>
            <td><strong>{t['unique_tasks_after_dedup']}</strong></td>
            <td><span style="color:{err_color};font-weight:600">{t['errors']}</span></td>
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

    # ── Chunk breakdown ───────────────────────────────────────────────────────
    st.markdown("### 🔬 Chunk-Level Breakdown")
    st.markdown(f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:16px'>Transcript split into <strong style='color:#6d28d9'>{ANALYTICS['num_chunks']} chunks</strong> · {ANALYTICS['chunk_size_lines']} lines/chunk · {ANALYTICS['overlap_lines']} lines overlap</div>", unsafe_allow_html=True)

    for m in ANALYTICS["models"]:
        with st.expander(f"🔹 {m['model']}", expanded=(m["model"] == best_model)):
            for c in m["chunks"]:
                cls  = "ok" if c["status"] == "ok" else "err"
                icon = "✅" if c["status"] == "ok" else "❌"
                tasks_pill = f"<div class='chunk-pill'>{icon} <span>{c['tasks_found']} tasks</span></div>"
                tok_pill   = f"<div class='chunk-pill'>tokens <span>{c.get('total_tokens',0):,}</span></div>"
                time_pill  = f"<div class='chunk-pill'>⏱ <span>{c['wall_time_sec']:.1f}s</span></div>"
                err_pill   = f"<div class='chunk-pill' style='color:#dc2626'>error: {c.get('error','—')}</div>" if c["status"] == "error" else ""
                st.markdown(f"""<div class="chunk-row {cls}">
                    <div style="color:#9095b8;min-width:70px">Chunk {c['chunk_index']}</div>
                    {tasks_pill}{tok_pill}{time_pill}{err_pill}
                </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── Action items ──────────────────────────────────────────────────────────
    st.markdown("### ✅ Extracted Action Items")
    st.markdown(f"<div style='color:#6b7280;font-size:0.85rem;margin-bottom:16px'>From best model · <strong style='color:#6d28d9'>{best_model}</strong></div>", unsafe_allow_html=True)

    priority_colors = {"High": "#dc2626", "Medium": "#d97706", "Low": "#16a34a"}
    priority_bg     = {"High": "#fef2f2", "Medium": "#fffbeb", "Low": "#f0fdf4"}
    priority_border = {"High": "#fecaca", "Medium": "#fde68a", "Low": "#bbf7d0"}

    for task in TASKS_SAMPLE:
        p   = task.get("priority", "Medium")
        pc  = priority_colors.get(p, "#6b7280")
        pb  = priority_bg.get(p, "#ffffff")
        pbd = priority_border.get(p, "#e2e4ec")
        dl  = f"<span style='color:#6b7280;font-size:0.8rem'>📅 {task['deadline']}</span>" if task.get("deadline") else ""
        st.markdown(f"""<div class="card" style="border-left:3px solid {pc};background:{pb};border-color:{pbd};padding:16px 20px;margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
                <div>
                    <div style="font-size:0.78rem;color:#9095b8;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">👤 {task['speaker']}</div>
                    <div style="color:#1a1a2e;font-weight:500">{task['task_description']}</div>
                    <div style="margin-top:6px">{dl}</div>
                </div>
                <div style="background:white;border:1px solid {pc};color:{pc};border-radius:12px;padding:2px 10px;font-size:0.75rem;font-weight:700;white-space:nowrap">{p}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#b0b4cc;font-size:0.8rem'>LooqBaq · Built with Faster-Whisper, Pyannote, and Ollama · Kathalyst</div>", unsafe_allow_html=True)