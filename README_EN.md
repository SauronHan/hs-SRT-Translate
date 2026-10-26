# hs-SRT-Translate

> **English** | [中文](README.md)

A completely local, zero-third-party-API-key-dependent Agent Skill for extracting original speech SRT subtitles and generating high-fidelity translations.

---

## 🌟 Key Features

- **100% Offline & Local Execution (Zero API Costs)**:
  - Audio extraction and speech-to-text recognition rely entirely on local `ffmpeg` and OpenAI `whisper`.
  - Semantic translation directly leverages the current AI Agent model itself, **requiring no third-party machine translation or LLM API keys**.
- **Identical Environment Footprint to `hs-media-to-md`**:
  - Built with pure Python standard library utilities and identical system prerequisites.
  - Cross-platform support for macOS, Windows, and Linux.
- **Two-Stage Context-Aware Translation**:
  - **Full-Context Comprehension & Glossary Consistency**: The Agent reads through the video's complete transcript first, identifying the overarching topic, speaker tone, and domain-specific terminology before translation begins.
  - **Anti-Truncation Chunking Architecture**: Automatically splits long subtitles into chunks to prevent model output truncation while preserving terminology consistency.
- **Strict Timestamp & Index Preservation (1:1 Alignment)**:
  - Verifies indices and timestamps across the entire pipeline, guaranteeing zero dropped lines, drift, or syntax corruption.
- **Triple-Deliverable Output**:
  - Automatically produces **Original Raw Subtitle (.raw.srt)**, **Target Language Subtitle (.srt)**, and **Bilingual Subtitle (.bilingual.srt)**.

---

## 🛠️ Prerequisites

Ensure the following tools are installed on your system (identical to `hs-media-to-md`):

1. **Python 3.8+**
2. **FFmpeg & FFprobe**:
   - macOS: `brew install ffmpeg`
   - Windows: `winget install Gyan.FFmpeg`
   - Linux: `sudo apt update && sudo apt install -y ffmpeg`
3. **OpenAI Whisper**:
   - `pip install openai-whisper`

---

## 📂 Deliverables

Processed files are saved in the **same directory as the input media file**:

| Filename | Format | Description |
| :--- | :--- | :--- |
| `<media_name>.<source_lang>.raw.srt` | SRT | **Original Speech Subtitle** extracted locally via Whisper. |
| `<media_name>.<target_lang>.srt` | SRT | **Target Language Subtitle** translated with deep context awareness and strict 1:1 timeline alignment. |
| `<media_name>.bilingual.srt` | SRT | **Bilingual Subtitle** (Target language on top, Source language below) ready for media players. |

---

## 📄 License

MIT License
