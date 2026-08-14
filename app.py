import streamlit as st
import time
from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain, ask_question


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Shiv AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PREMIUM STREAMLIT CSS
#
# IMPORTANT:
# There is NO custom HTML UI below.
# Only CSS is injected into Streamlit.
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap'
    );

    html,
    body,
    [class*="css"] {
        font-family: "Inter", sans-serif !important;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 5% 0%,
                rgba(124, 58, 237, 0.14),
                transparent 28%
            ),
            radial-gradient(
                circle at 95% 10%,
                rgba(6, 182, 212, 0.08),
                transparent 25%
            ),
            #050507 !important;
    }


    /* ========================================================
       BACKGROUND GRID
       ======================================================== */

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;

        background-image:
            linear-gradient(
                rgba(139, 92, 246, 0.025) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(139, 92, 246, 0.025) 1px,
                transparent 1px
            );

        background-size: 44px 44px;

        pointer-events: none;

        z-index: 0;
    }


    /* ========================================================
       MAIN WIDTH
       ======================================================== */

    .block-container {
        max-width: 1450px !important;

        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
    }


    /* ========================================================
       HEADINGS
       ======================================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        font-family:
            "Space Grotesk",
            sans-serif !important;

        color:
            #f8fafc !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #090a0f,
                #050507
            ) !important;

        border-right:
            1px solid
            rgba(255,255,255,0.08) !important;
    }


    [data-testid="stSidebar"] * {
        color:
            #f8fafc !important;
    }


    /* ========================================================
       SIDEBAR INPUT
       ======================================================== */

    [data-testid="stSidebar"] input {
        background:
            rgba(255,255,255,0.04) !important;

        border:
            1px solid
            rgba(255,255,255,0.10) !important;

        border-radius:
            12px !important;

        color:
            #ffffff !important;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        width: 100%;

        min-height: 45px;

        border-radius: 12px !important;

        border:
            1px solid
            rgba(255,255,255,0.08) !important;

        background:
            linear-gradient(
                135deg,
                #7c3aed,
                #4f46e5
            ) !important;

        color:
            #ffffff !important;

        font-family:
            "Space Grotesk",
            sans-serif !important;

        font-weight:
            700 !important;

        transition:
            all 0.2s ease !important;
    }


    .stButton > button:hover {
        transform:
            translateY(-2px);

        box-shadow:
            0 12px 30px
            rgba(124,58,237,0.35);
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div {
        background:
            rgba(255,255,255,0.035) !important;

        border:
            1px solid
            rgba(255,255,255,0.10) !important;

        border-radius:
            12px !important;

        color:
            #ffffff !important;
    }


    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color:
            #8b5cf6 !important;

        box-shadow:
            0 0 0 3px
            rgba(139,92,246,0.12) !important;
    }


    /* ========================================================
       NATIVE CONTAINERS
       ======================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        background:
            linear-gradient(
                145deg,
                rgba(255,255,255,0.045),
                rgba(255,255,255,0.015)
            ) !important;

        border:
            1px solid
            rgba(255,255,255,0.09) !important;

        border-radius:
            20px !important;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    [data-testid="stMetric"] {
        background:
            rgba(255,255,255,0.025);

        border:
            1px solid
            rgba(255,255,255,0.07);

        border-radius:
            16px;

        padding:
            16px;
    }


    [data-testid="stMetricLabel"] {
        color:
            #8992a3 !important;
    }


    [data-testid="stMetricValue"] {
        color:
            #f8fafc !important;

        font-family:
            "Space Grotesk",
            sans-serif !important;
    }


    /* ========================================================
       TABS
       ======================================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap:
            8px;

        background:
            rgba(255,255,255,0.025);

        padding:
            6px;

        border-radius:
            14px;
    }


    .stTabs [data-baseweb="tab"] {
        border-radius:
            10px;

        padding:
            10px 18px;

        color:
            #8992a3;
    }


    .stTabs [aria-selected="true"] {
        background:
            rgba(139,92,246,0.16) !important;

        color:
            #c4b5fd !important;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    [data-testid="stExpander"] {
        background:
            rgba(255,255,255,0.025) !important;

        border:
            1px solid
            rgba(255,255,255,0.08) !important;

        border-radius:
            16px !important;
    }


    /* ========================================================
       ALERTS
       ======================================================== */

    [data-testid="stAlert"] {
        border-radius:
            14px !important;
    }


    /* ========================================================
       CHAT
       ======================================================== */

    [data-testid="stChatMessage"] {
        border:
            1px solid
            rgba(255,255,255,0.06);

        border-radius:
            16px;

        margin-bottom:
            10px;

        background:
            rgba(255,255,255,0.025);
    }


    /* ========================================================
       DIVIDERS
       ======================================================== */

    hr {
        border:
            none !important;

        border-top:
            1px solid
            rgba(255,255,255,0.07) !important;

        margin:
            1.5rem 0 !important;
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {
        width:
            6px;
    }

    ::-webkit-scrollbar-track {
        background:
            #050507;
    }

    ::-webkit-scrollbar-thumb {
        background:
            rgba(255,255,255,0.14);

        border-radius:
            10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background:
            #8b5cf6;
    }


    /* ========================================================
       MOBILE
       ======================================================== */

    @media (max-width: 768px) {

        .block-container {
            padding-left:
                1rem !important;

            padding-right:
                1rem !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():

    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "# 🎬 Shiv AI"
    )

    st.caption(
        "VIDEO INTELLIGENCE PLATFORM"
    )

    st.divider()


    st.markdown(
        "### 🎯 Workspace"
    )

    st.caption(
        "Provide a YouTube URL or local audio/video file."
    )


    source = st.text_input(
        "YouTube URL / File Path",
        placeholder="https://youtube.com/watch?...",
    )


    language = st.selectbox(
        "🌐 Language",
        [
            "english",
            "hinglish",
        ],
        index=0,
    )


    run_btn = st.button(
        "⚡  ANALYSE VIDEO",
        use_container_width=True,
    )


    st.divider()


    # ========================================================
    # PIPELINE STATUS
    # ========================================================

    st.markdown(
        "### ⚙️ Pipeline"
    )


    pipeline_items = [
        (
            "audio",
            "🔊",
            "Audio Processing"
        ),
        (
            "transcript",
            "📝",
            "Transcription"
        ),
        (
            "title",
            "🏷️",
            "Title Generation"
        ),
        (
            "summary",
            "📋",
            "Summarisation"
        ),
        (
            "extract",
            "🔍",
            "Insight Extraction"
        ),
        (
            "rag",
            "🧠",
            "RAG Engine"
        ),
    ]


    if st.session_state.pipeline_done:

        st.success(
            "Pipeline completed"
        )


    for key, icon, label in pipeline_items:

        status = st.session_state.pipeline_steps.get(
            key,
            "pending"
        )


        if status == "done":

            st.success(
                f"{icon} {label}",
                icon="✅",
            )

        elif status == "active":

            st.info(
                f"{icon} {label}",
                icon="⏳",
            )

        else:

            st.caption(
                f"○ {icon} {label}"
            )


    st.divider()


    # ========================================================
    # DEVELOPER
    # ========================================================

    st.markdown(
        "### 👨‍💻 Developer"
    )


    st.markdown(
        "**Shiv Shankar Tiwari**"
    )

    st.caption(
        "Data Analyst • AI/ML Developer"
    )

    st.caption(
        "Python • AI • ML • NLP • RAG • "
        "Prompt Engineering"
    )


    st.divider()


    st.caption(
        "Shiv AI Video Assistant"
    )

    st.caption(
        "Built with Python + Streamlit"
    )


# ============================================================
# HERO SECTION
# ============================================================

st.markdown(
    "# 🎬 Shiv AI Video Assistant"
)

st.markdown(
    "### Transform videos into searchable intelligence."
)

st.write(
    """
    **Transcribe → Summarise → Extract Insights → Chat with your Video**
    
    Shiv AI converts long-form videos and meetings into structured
    knowledge using speech recognition, NLP, LLMs and Retrieval-Augmented
    Generation.
    """
)


# ============================================================
# HERO METRICS
# ============================================================

hero_cols = st.columns(
    4,
    gap="medium"
)


with hero_cols[0]:

    st.metric(
        "🎙️ Transcription",
        "AI Powered",
    )


with hero_cols[1]:

    st.metric(
        "📋 Summarisation",
        "Automatic",
    )


with hero_cols[2]:

    st.metric(
        "🧠 RAG",
        "Interactive",
    )


with hero_cols[3]:

    st.metric(
        "⚡ Pipeline",
        "End-to-End",
    )


st.markdown(
    ""
)

st.divider()


# ============================================================
# FEATURE OVERVIEW
# ============================================================

st.markdown(
    "## ✨ What Shiv AI Can Do"
)


feature_cols = st.columns(
    4,
    gap="medium"
)


with feature_cols[0]:

    with st.container(border=True):

        st.markdown(
            "### 🎙️"
        )

        st.markdown(
            "**Smart Transcription**"
        )

        st.caption(
            "Convert long videos and meetings "
            "into searchable text."
        )


with feature_cols[1]:

    with st.container(border=True):

        st.markdown(
            "### ⚡"
        )

        st.markdown(
            "**AI Summaries**"
        )

        st.caption(
            "Turn lengthy conversations into "
            "concise, useful summaries."
        )


with feature_cols[2]:

    with st.container(border=True):

        st.markdown(
            "### 🧠"
        )

        st.markdown(
            "**RAG Intelligence**"
        )

        st.caption(
            "Ask natural-language questions "
            "about your video."
        )


with feature_cols[3]:

    with st.container(border=True):

        st.markdown(
            "### 📊"
        )

        st.markdown(
            "**Insight Extraction**"
        )

        st.caption(
            "Find decisions, action items "
            "and open questions."
        )


st.markdown(
    ""
)


# ============================================================
# RUN AI PIPELINE
#
# SAME LOGIC AS YOUR ORIGINAL APP
# ============================================================

if run_btn:

    if not source.strip():

        st.error(
            "Please enter a YouTube URL or local file path."
        )

    else:

        st.session_state.pipeline_done = False

        st.session_state.result = None

        st.session_state.chat_history = []

        st.session_state.pipeline_steps = {}


        progress_placeholder = st.empty()


        def update_step(
            key,
            state
        ):

            st.session_state.pipeline_steps[
                key
            ] = state


        try:

            with progress_placeholder.container():

                st.info(
                    "⚙️ Shiv AI is processing your video..."
                )


            # =================================================
            # AUDIO
            # =================================================

            update_step(
                "audio",
                "active"
            )

            chunks = process_input(
                source
            )

            update_step(
                "audio",
                "done"
            )


            # =================================================
            # TRANSCRIPTION
            # =================================================

            update_step(
                "transcript",
                "active"
            )

            transcript = transcribe_all(
                chunks,
                language
            )

            update_step(
                "transcript",
                "done"
            )


            # =================================================
            # TITLE
            # =================================================

            update_step(
                "title",
                "active"
            )

            title = generate_title(
                transcript
            )

            update_step(
                "title",
                "done"
            )


            # =================================================
            # SUMMARY
            # =================================================

            update_step(
                "summary",
                "active"
            )

            summary = summarize(
                transcript
            )

            update_step(
                "summary",
                "done"
            )


            # =================================================
            # EXTRACTION
            # =================================================

            update_step(
                "extract",
                "active"
            )

            action_items = extract_action_items(
                transcript
            )

            decisions = extract_key_decisions(
                transcript
            )

            questions = extract_questions(
                transcript
            )

            update_step(
                "extract",
                "done"
            )


            # =================================================
            # RAG
            # =================================================

            update_step(
                "rag",
                "active"
            )

            rag_chain = build_rag_chain(
                transcript
            )

            update_step(
                "rag",
                "done"
            )


            # =================================================
            # STORE RESULTS
            # =================================================

            st.session_state.result = {

                "title":
                    title,

                "transcript":
                    transcript,

                "summary":
                    summary,

                "action_items":
                    action_items,

                "key_decisions":
                    decisions,

                "open_questions":
                    questions,

                "rag_chain":
                    rag_chain,

            }


            st.session_state.pipeline_done = True


            progress_placeholder.success(
                "✅ Analysis completed successfully!"
            )


            time.sleep(
                0.5
            )


            progress_placeholder.empty()


            st.rerun()


        except Exception as e:

            for key in [
                "audio",
                "transcript",
                "title",
                "summary",
                "extract",
                "rag",
            ]:

                if (
                    st.session_state
                    .pipeline_steps
                    .get(key)
                    == "active"
                ):

                    st.session_state.pipeline_steps[
                        key
                    ] = "pending"


            progress_placeholder.error(
                f"❌ Processing failed: {e}"
            )


# ============================================================
# RESULTS
# ============================================================

if st.session_state.result:

    r = st.session_state.result


    # ========================================================
    # ANALYSIS HEADER
    # ========================================================

    st.success(
        "🎉 Video analysis completed"
    )


    with st.container(border=True):

        st.caption(
            "SESSION TITLE"
        )

        st.title(
            r["title"]
        )


    st.markdown(
        ""
    )


    # ========================================================
    # RESULT METRICS
    # ========================================================

    result_cols = st.columns(
        4,
        gap="medium"
    )


    with result_cols[0]:

        st.metric(
            "🎙️ Transcript",
            "READY"
        )


    with result_cols[1]:

        st.metric(
            "📋 Summary",
            "READY"
        )


    with result_cols[2]:

        st.metric(
            "🔍 Insights",
            "EXTRACTED"
        )


    with result_cols[3]:

        st.metric(
            "🧠 RAG Chat",
            "ACTIVE"
        )


    st.markdown(
        ""
    )


    # ========================================================
    # SUMMARY + TRANSCRIPT
    # ========================================================

    summary_col, transcript_col = st.columns(
        [3, 2],
        gap="medium"
    )


    with summary_col:

        with st.container(border=True):

            st.markdown(
                "## 📋 AI Summary"
            )

            st.write(
                r["summary"]
            )


    with transcript_col:

        with st.container(border=True):

            st.markdown(
                "## 📝 Transcript"
            )

            with st.expander(
                "Open full transcript"
            ):

                st.text_area(
                    "Transcript",
                    r["transcript"],
                    height=350,
                    label_visibility="collapsed",
                )


    st.markdown(
        ""
    )


    # ========================================================
    # INSIGHTS
    # ========================================================

    st.markdown(
        "## 🔎 Intelligence Extracted"
    )


    insight_tabs = st.tabs(
        [
            "✅ Action Items",
            "🔑 Key Decisions",
            "❓ Open Questions",
        ]
    )


    with insight_tabs[0]:

        with st.container(border=True):

            st.markdown(
                "### ✅ Action Items"
            )

            st.write(
                r["action_items"]
            )


    with insight_tabs[1]:

        with st.container(border=True):

            st.markdown(
                "### 🔑 Key Decisions"
            )

            st.write(
                r["key_decisions"]
            )


    with insight_tabs[2]:

        with st.container(border=True):

            st.markdown(
                "### ❓ Open Questions"
            )

            st.write(
                r["open_questions"]
            )


    st.divider()


    # ========================================================
    # RAG CHAT
    # ========================================================

    st.markdown(
        "## 💬 Chat with Your Video"
    )

    st.caption(
        "Ask questions about the analysed transcript, "
        "decisions, action items and discussion."
    )


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    if st.session_state.chat_history:

        for message in st.session_state.chat_history:

            if message["role"] == "user":

                with st.chat_message(
                    "user"
                ):

                    st.write(
                        message["content"]
                    )

            else:

                with st.chat_message(
                    "assistant"
                ):

                    st.write(
                        message["content"]
                    )


    else:

        with st.container(border=True):

            st.markdown(
                "### 🧠 Shiv AI is ready"
            )

            st.caption(
                "Ask anything about your video."
            )

            st.caption(
                "Example: What were the main decisions?"
            )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    user_input = st.chat_input(
        "Ask Shiv AI about this video..."
    )


    if user_input:

        with st.chat_message(
            "user"
        ):

            st.write(
                user_input
            )


        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Shiv AI is thinking..."
            ):

                answer = ask_question(
                    r["rag_chain"],
                    user_input.strip()
                )

            st.write(
                answer
            )


        st.session_state.chat_history.append(
            {
                "role":
                    "user",

                "content":
                    user_input.strip(),
            }
        )


        st.session_state.chat_history.append(
            {
                "role":
                    "assistant",

                "content":
                    answer,
            }
        )


        st.rerun()


    if st.session_state.chat_history:

        st.markdown(
            ""
        )

        if st.button(
            "🗑️ Clear Conversation"
        ):

            st.session_state.chat_history = []

            st.rerun()


# ============================================================
# EMPTY STATE
# ============================================================

else:

    st.markdown(
        ""
    )


    with st.container(
        border=True
    ):

        st.markdown(
            "# 🎬"
        )

        st.markdown(
            "## Ready to Analyse"
        )

        st.write(
            """
            Your AI video intelligence workspace is ready.

            Paste a **YouTube URL** or provide a **local video/audio
            path** in the sidebar, select the language, and click
            **Analyse Video**.
            """
        )


        empty_cols = st.columns(
            3,
            gap="medium"
        )


        with empty_cols[0]:

            st.info(
                "🎙️\n\n"
                "**Transcription**\n\n"
                "Convert speech into searchable text."
            )


        with empty_cols[1]:

            st.info(
                "📋\n\n"
                "**Summarisation**\n\n"
                "Generate concise AI-powered summaries."
            )


        with empty_cols[2]:

            st.info(
                "🧠\n\n"
                "**RAG Chat**\n\n"
                "Ask questions directly about the video."
            )


    st.markdown(
        ""
    )


    # ========================================================
    # DEVELOPER SECTION
    # ========================================================

    st.markdown(
        "## 👨‍💻 About the Developer"
    )


    developer_col1, developer_col2 = st.columns(
        [1, 2],
        gap="medium"
    )


    with developer_col1:

        with st.container(
            border=True
        ):

            st.markdown(
                "# 👨‍💻"
            )

            st.markdown(
                "### Shiv Shankar Tiwari"
            )

            st.markdown(
                "**Data Analyst & AI/ML Developer**"
            )

            st.caption(
                "Building intelligent applications with "
                "Python, AI, machine learning, NLP, RAG "
                "and prompt engineering."
            )


    with developer_col2:

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🚀 About Shiv AI Video Assistant"
            )

            st.write(
                """
                **Shiv AI Video Assistant** is an end-to-end
                AI application designed to transform long-form
                video and meeting content into structured,
                searchable knowledge.

                The system combines **speech transcription,
                natural language processing, LLM-powered
                summarisation, insight extraction and
                Retrieval-Augmented Generation**.

                Users can upload or provide video content,
                receive an intelligent analysis, and then
                interact with the processed content through
                an AI-powered conversational interface.
                """
            )


    st.markdown(
        ""
    )


    # ========================================================
    # TECH STACK
    # ========================================================

    st.markdown(
        "### 🛠️ Technology Stack"
    )


    tech_cols = st.columns(
        6,
        gap="small"
    )


    technologies = [
        ("🐍", "Python"),
        ("🤖", "AI / ML"),
        ("🧠", "NLP"),
        ("🔎", "RAG"),
        ("⚡", "Mistral"),
        ("🎨", "Streamlit"),
    ]


    for col, (icon, name) in zip(
        tech_cols,
        technologies
    ):

        with col:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {icon}"
                )

                st.caption(
                    name
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(
    "🎬 Shiv AI Video Assistant  •  "
    "Built with Python + Streamlit + AI + RAG"
)


st.caption(
    "Crafted by Shiv Shankar Tiwari"
)