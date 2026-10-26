# hs-SRT-Translate

> [English](README_EN.md) | **中文**

完全本地运行、无第三方 API KEY 依赖的高保真音视频原声字幕提取与智能翻译 Agent Skill。

---

## 🌟 核心特性

- **100% 本地离线运行，零 API 成本**：
  - 音频流提取与语音转录完全依赖本地的 `ffmpeg` 与 OpenAI `whisper` 引擎。
  - 语义翻译直接调用当前 AI Agent 自身的模型推理能力，**无需购买或配置任何第三方机翻或大模型 API KEY**。
- **环境要求与理念承袭**：
  - 纯 Python 标准库辅助工具，与 `hs-media-to-md` 保持完全一致的基础环境要求。
  - 跨平台原生兼容（macOS / Windows / Linux）。
- **两阶段语义感知翻译（告别机械生硬的机翻）**：
  - **背景通读与术语统一**：Agent 在动笔前先通读整段音视频文本，精准掌握主题背景、演讲风格与核心专有名词，建立一致性术语表（Glossary）。
  - **防截断保真翻译**：内置自适应分批切分与追加写入机制，彻底杜绝长视频翻译截断问题。
- **严密的时间轴保障（1:1 绝对对齐）**：
  - 时间戳与序号全流程校验，确保与原声音频完全同步，不丢行、不合并、不偏移。
- **一次处理，三重交付**：
  - 自动输出 **原声音频字幕 (.raw.srt)**、**目标语言纯译文字幕 (.srt)** 与 **双语对照同屏字幕 (.bilingual.srt)**。

---

## 🛠️ 前置环境准备 (Prerequisites)

在安装与使用本 Skill 之前，请确保您的系统中已安装并配置好以下基础运行环境（与 `hs-media-to-md` 完全一致）：

### 1. Python 环境
- 需要 **Python 3.8 或更高版本**。
- 请确保 `python`（或 `python3`）已添加到系统的环境变量（PATH）中。

### 2. 安装 FFmpeg 与 FFprobe
本 Skill 使用 FFmpeg 进行音视频流检查与音频标准化转码（16kHz WAV）。

- **macOS**（推荐使用 Homebrew）：
  ```bash
  brew install ffmpeg
  ```
- **Windows**（推荐使用 winget 或 Scoop）：
  ```powershell
  winget install Gyan.FFmpeg
  # 或者使用 Scoop: scoop install ffmpeg
  ```
- **Linux (Ubuntu/Debian)**：
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```

> **验证安装**：在终端运行 `ffmpeg -version` 和 `ffprobe -version`，能正常输出版本号即表示安装成功。

### 3. 安装 OpenAI Whisper
本 Skill 使用 OpenAI Whisper 进行本地高精度离线语音识别：

```bash
pip install openai-whisper
```

> **GPU 加速提示**：
> - **Windows / Linux (NVIDIA 显卡)**：安装匹配您 CUDA 版本的 PyTorch 即可开启 GPU 极速推理，请参考 [PyTorch 官网](https://pytorch.org/get-started/locally/)。
> - **macOS (Apple Silicon M 系列芯片)**：Whisper 会自动结合 MPS / CPU 高效运行。

---

## 🚀 安装与使用

### 安装 Skill
将本目录放置在您的 Agent Skills 系统目录中，或直接在项目中使用软链接挂载至 `.agent/skills/`：

```bash
# 进入您的 Agent 技能目录并软链接或复制
ln -s /path/to/hs-SRT-Translate ~/.gemini/antigravity/skills/hs-SRT-Translate
```

### 使用方式与交互示例

直接在 AI 聊天对话中发送音视频文件路径，并提出字幕提取或翻译需求：

#### 示例 1：默认交互模式（自动询问）
> **用户**：“帮我处理一下这个视频：`~/Videos/DeepLearning_Intro.mp4`”  
> **Agent**：“已收到音视频处理请求。请确认音视频的**原始语言**和需要翻译的**目标语言**（默认原始语言为**英文**，目标语言为**简体中文**）。如果直接使用默认配置，请回复‘确认’。”  
> **用户**：“确认使用默认。”  
> *(Agent 自动调用本地 whisper 生成英文原声字幕，分析上下文后高质量翻译为中文，并生成中英双语字幕)*

#### 示例 2：一句话直接指定语种（免打扰直达）
> **用户**：“把这个日语视频提取字幕并翻译成中文：`xxxxx.mp4`”  
> *(Agent 自动识别源语言为 ja、目标语言为 zh，跳过询问直接执行提取与翻译)*

---

## 📂 处理输出结果 (Outputs)

任务处理完成后，将在**与原媒体文件相同的目录下**生成以下标准成果文件：

| 文件名称 | 格式 | 说明 |
| :--- | :--- | :--- |
| `<原文件名>.<源语言>.raw.srt` | SRT 字幕 | **原声语音识别字幕**<br>• 本地 Whisper 模型生成的原汁原味原声音轨字幕，作为基准核验底本 |
| `<原文件名>.<目标语言>.srt` | SRT 字幕 | **目标语言纯译文字幕**<br>• 基于深度背景与术语理解的高质量翻译字幕<br>• 序号与时间戳与原片 100% 严格对齐，单行排版符合屏幕观影视角 |
| `<原文件名>.bilingual.srt` | SRT 字幕 | **双语同屏对照字幕**<br>• 上方显示目标语言译文，下方显示源语言原文<br>• 适合专业学习、跨语言对照与多媒体播放器直接载入观影 |

---

## 📄 许可证

MIT License
