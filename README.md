# 🎬 Shiv AI Video Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Shiv%20AI-Video%20Intelligence-7c3aed?style=for-the-badge&logo=streamlit&logoColor=white" alt="Shiv AI" />
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/AI-RAG-8B5CF6?style=for-the-badge" alt="RAG" />
</p>

<p align="center">
  <strong>Transform long-form videos and meetings into structured, searchable intelligence.</strong>
</p>

<p align="center">
  <a href="https://shiv-ai-video-assistant.streamlit.app/">🚀 Live Demo</a>
  &nbsp;•&nbsp;
  <a href="https://github.com/sandilyashivshankar/Shiv-AI-Video-Assistant">📦 Source Code</a>
</p>

---

## 🌟 Overview

**Shiv AI Video Assistant** is an end-to-end AI application that converts video and meeting content into actionable knowledge.

Instead of watching an entire recording again, users can process content into:

- 🎙️ **Transcripts**
- 📝 **AI-generated summaries**
- ✅ **Action items**
- 🔑 **Key decisions**
- ❓ **Open questions**
- 🧠 **RAG-powered conversational Q&A**

The project combines speech-to-text, LLM orchestration, vector retrieval, and a Streamlit interface into a single workflow.

> **Project goal:** reduce the time required to understand long meetings, lectures, interviews, presentations, and other spoken-content recordings.

---

## 🚀 Live Application

### [Open Shiv AI Video Assistant](https://shiv-ai-video-assistant.streamlit.app/)

You can use the deployed application to explore the complete workflow and interact with analysed content.

---

## ✨ Core Capabilities

| Capability | What it does |
|---|---|
| 🎥 Video Input | Accepts supported YouTube URLs and local audio/video files |
| 🎙️ Transcription | Uses local Whisper for English transcription |
| 🇮🇳 Hinglish Support | Uses Sarvam AI for Hinglish-to-English speech translation |
| 📋 Summarisation | Produces concise AI summaries from transcripts |
| ✅ Action Items | Extracts tasks and follow-up work |
| 🔑 Decisions | Identifies important decisions from the conversation |
| ❓ Questions | Surfaces unresolved or important questions |
| 🧠 RAG Chat | Enables question-answering over the processed transcript |
| 🔎 Retrieval | Uses vector search to retrieve relevant transcript context |
| 🖥️ Streamlit UI | Provides a polished interactive AI workspace |

---

## 🧩 How It Works

```text
                    ┌──────────────────────┐
                    │   YouTube / Local    │
                    │     Audio / Video    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Audio Processing   │
                    │   yt-dlp + FFmpeg     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Speech Processing  │
                    │ Whisper / Sarvam AI  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Transcript      │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼───────────────┐
                ▼              ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │  Summary     │ │  Extraction  │ │  Vector RAG  │
        │   Mistral    │ │ Actions /    │ │  Chroma +    │
        │              │ │ Decisions /  │ │  Embeddings  │
        │              │ │ Questions    │ │              │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                 │                │
               └─────────────────┼────────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │   Shiv AI Workspace  │
                    │   Dashboard + Chat   │
                    └──────────────────────┘
```

---

## 🛠️ Technology Stack

### AI / Machine Learning

- **OpenAI Whisper** — local speech-to-text
- **Sarvam AI** — Hinglish speech translation / transcription path
- **Mistral AI** — LLM-based summarisation and insight generation
- **Sentence Transformers** — text embeddings
- **ChromaDB** — vector storage and retrieval

### Application

- **Python**
- **Streamlit**
- **LangChain / LangChain Community**
- **yt-dlp**
- **FFmpeg**
- **Requests**
- **python-dotenv**

### Output / Utilities

- **ReportLab / FPDF2** for document generation utilities
- **NumPy / tqdm** for supporting utilities

---

## 📁 Project Structure

```text
Shiv-AI-Video-Assistant/
│
├── app.py
├── requirements.txt
├── packages.txt
├── runtime.txt
├── README.md
├── .gitignore
│
├── core/
│   ├── __init__.py
│   ├── extractor.py
│   ├── rag_engine.py
│   ├── summarizer.py
│   ├── transcriber.py
│   └── vector_store.py
│
└── utils/
    ├── __init__.py
    └── audio_processor.py
```

---

## ⚡ Key User Flow

### 1. Provide content

Paste a supported YouTube URL or provide a local audio/video path.

### 2. Select language

Choose:

- **English** → local Whisper transcription
- **Hinglish** → Sarvam AI transcription/translation flow

### 3. Run analysis

The application processes the recording, generates a transcript, and prepares the AI knowledge layer.

### 4. Explore insights

Review the generated:

- Summary
- Action items
- Key decisions
- Open questions

### 5. Chat with the video

Ask questions naturally and retrieve answers from the analysed transcript through the RAG pipeline.

---

## 🧠 RAG Architecture

The conversational layer follows the general pattern:

```text
Transcript
   ↓
Text Splitting
   ↓
Embeddings
   ↓
Chroma Vector Store
   ↓
Retriever
   ↓
Relevant Context
   ↓
Mistral / LLM Reasoning
   ↓
Answer
```

This makes it possible to ask focused questions instead of manually searching through a long transcript.

---

## 📊 What Makes This Project Interesting

Shiv AI is more than a transcription tool. It connects multiple AI capabilities into one practical product:

**Speech → Language Understanding → Information Extraction → Retrieval → Conversational AI**

That makes it suitable as a portfolio project for demonstrating applied AI engineering, NLP, data processing, RAG, and product-oriented problem solving.

---

## 👨‍💻 About the Developer

### Shiv Shankar Tiwari

**Data Analyst | AI/ML Developer | Prompt Engineering Enthusiast**

I am a technology-focused developer interested in building practical data and AI solutions that solve real-world problems.

My interests include:

- 📊 Data Analytics
- 🤖 Artificial Intelligence
- 🧠 Machine Learning
- 💬 Natural Language Processing
- 🔎 Retrieval-Augmented Generation (RAG)
- ✨ Generative AI
- 🧩 Prompt Engineering
- 🐍 Python-based intelligent applications

I enjoy turning complex technical ideas into usable applications with a strong focus on problem solving, experimentation, and product thinking.

### Developer Links

<p>
  <a href="https://github.com/sandilyashivshankar">GitHub</a> •
  <a href="https://www.linkedin.com/in/shiv-shankar-tiwari-a4054a282/">LinkedIn</a>
</p>

---

## 🔐 Environment Variables & Secrets

The project is designed to keep API credentials outside source code.

### Local `.env`

Example:

```env
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key
WHISPER_MODEL=small
SARVAM_STT_MODEL=saaras:v2.5
```

### Streamlit Cloud

Configure the same values through **Streamlit Secrets** rather than committing secrets to GitHub.

> **Never commit `.env`, API keys, browser cookies, or authentication files to the repository.**

---

## 💻 Local Development

### Prerequisites

- Python 3.12 recommended for the deployed configuration
- `uv` package manager
- FFmpeg installed locally

### Setup with `uv`

```bash
# Clone the repository
git clone https://github.com/sandilyashivshankar/Shiv-AI-Video-Assistant.git

# Enter the project
cd Shiv-AI-Video-Assistant

# Create the environment and install dependencies
uv sync
```

If your environment is already created:

```bash
uv run streamlit run app.py
```

The app will be available at:

```text
http://localhost:8501
```

---

## ☁️ Streamlit Cloud Deployment

This project is prepared for Streamlit deployment with:

```text
requirements.txt   → Python dependencies
packages.txt       → Linux system packages such as FFmpeg
runtime.txt        → Python runtime selection
```

Recommended deployment flow:

```text
GitHub Repository
       ↓
Streamlit Cloud
       ↓
Install requirements.txt
       ↓
Install packages.txt
       ↓
Start app.py
```

For API credentials, use Streamlit Cloud's **Secrets** configuration.

---

## ▶️ Example Questions

After analysis, you can ask questions such as:

```text
What are the main points discussed?

What decisions were made?

What action items were assigned?

What questions remain unanswered?

Give me a concise summary of the meeting.

What was the most important conclusion?
```

---

## 🔭 Future Improvements

Potential next-generation improvements include:

- 🎞️ Native video upload UI
- 👥 Speaker diarization
- ⏱️ Timestamp-aware answers
- 📌 Clickable transcript references
- 📤 One-click PDF / DOCX reports
- 🧠 Long-term project memory
- 🔐 User authentication
- 📚 Multi-video knowledge bases
- 📊 Analytics dashboard for meetings
- 🌐 Multilingual UI and transcription expansion

---

## 🧪 Project Status

**Status:** Active portfolio project / deployed prototype

The application is being actively refined around AI reliability, cloud deployment, transcript processing, and user experience.

---

## 🙌 Why I Built This

Long meetings, lectures, interviews, and presentations contain valuable information—but consuming them repeatedly is inefficient.

**Shiv AI Video Assistant** was created to make that information easier to access:

> **Watch less. Understand faster. Ask better questions.**

---

## ⭐ Support the Project

If this project is useful or interesting, consider:

- ⭐ starring the repository
- 🍴 exploring the code
- 💡 opening an issue with ideas
- 🤝 contributing improvements

---

## 📌 Links

| Resource | Link |
|---|---|
| 🚀 Live App | https://shiv-ai-video-assistant.streamlit.app/ |
| 📦 GitHub Repository | https://github.com/sandilyashivshankar/Shiv-AI-Video-Assistant |
| 👨‍💻 Developer GitHub | https://github.com/sandilyashivshankar |
| 💼 LinkedIn | https://www.linkedin.com/in/shiv-shankar-tiwari-a4054a282/ |

---

<p align="center">
  <strong>Built with Python • AI • RAG • Streamlit</strong><br/>
  Crafted by <strong>Shiv Shankar Tiwari</strong>
</p>
