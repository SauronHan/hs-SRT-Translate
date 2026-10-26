#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_srt.py
基于本地音视频文件，利用 ffmpeg 抽取音频并调用本地 Whisper 引擎生成原声 SRT 字幕文件。
完全本地离线运行，无需配置任何第三方 API KEY。
跨平台兼容 Windows / macOS / Linux。
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def print_err(msg: str) -> None:
    print(f"\033[91m[错误]\033[0m {msg}", file=sys.stderr)


def print_info(msg: str) -> None:
    print(f"\033[92m[信息]\033[0m {msg}")


def check_prerequisites() -> None:
    """检查必要的命令行工具是否已安装并在 PATH 中。"""
    missing = [tool for tool in ["ffmpeg", "ffprobe", "whisper"] if not shutil.which(tool)]
    if missing:
        print_err(f"系统中缺少必要工具: {', '.join(missing)}")
        print("💡 请参考本项目 README.md 中的「前置环境准备」完成安装配置后再试。")
        sys.exit(1)


def probe_media_streams(media_path: Path) -> dict:
    """使用 ffprobe 检查音视频流信息，验证是否存在音轨，并排除专辑封面干扰。"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(media_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
    except Exception as e:
        print_err(f"无法读取媒体文件元数据: {e}")
        sys.exit(1)

    streams = data.get("streams", [])
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    has_video = any(
        s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic", 0) == 0
        for s in streams
    )

    if not has_audio:
        print_err(f"文件 '{media_path.name}' 未检测到音频流（可能是无声视频），无法生成字幕。")
        sys.exit(1)

    duration_str = data.get("format", {}).get("duration", "0")
    try:
        duration = float(duration_str)
    except ValueError:
        duration = 0.0

    return {
        "media_type": "视频" if has_video else "音频",
        "duration": duration
    }


def extract_wav_audio(media_path: Path, output_wav: Path) -> None:
    """将视频或音频统一转为 16kHz 单声道 WAV 音频，确保 Whisper 获得最佳输入。"""
    print_info("正在提取并转换音频流 (16kHz 单声道 WAV)...")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(media_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_wav)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print_err(f"音频提取失败: {e.stderr}")
        sys.exit(1)


def run_whisper_transcribe(audio_wav: Path, output_dir: Path, model: str, language: str = "en", word_timestamps: bool = True) -> Path:
    """调用本地 whisper 生成 srt 格式字幕文件。"""
    precision_mode = "开启 (精确切除前置静音与配乐等待)" if word_timestamps else "关闭 (粗粒度段落)"
    print_info(f"正在使用本地 Whisper 引擎生成原声 SRT (模型: {model}, 语言: {language}, 词级时间戳: {precision_mode})...")
    cmd = [
        "whisper",
        str(audio_wav),
        "--model", model,
        "--output_format", "srt",
        "--output_dir", str(output_dir),
        "--verbose", "False"
    ]
    if word_timestamps:
        cmd.extend(["--word_timestamps", "True"])
    if language and language.lower() != "auto":
        cmd.extend(["--language", language])

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print_err(f"Whisper 执行失败，退出码: {e.returncode}")
        sys.exit(1)

    # 默认 whisper 输出文件名是 <audio_wav.stem>.srt
    generated_srt = output_dir / f"{audio_wav.stem}.srt"
    return generated_srt


def cleanup_temp_files(audio_wav: Path, keep_audio: bool) -> None:
    """清理提取音频过程中产生的临时中间文件。"""
    if not keep_audio and audio_wav.exists():
        try:
            audio_wav.unlink()
            print_info("已清理中间临时 WAV 音频文件。")
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="基于本地音视频抽取原声 SRT 字幕文件工具")
    parser.add_argument("media_path", help="本地音视频文件的路径")
    parser.add_argument("--source-lang", default="en", help="原声语言代码（如 en, zh, ja, ko, fr, de 等，默认: en）")
    parser.add_argument("--model", default="small", help="Whisper 模型规格 (默认: small, 可选: base, small, medium, turbo, large-v3)")
    parser.add_argument("--no-word-timestamps", action="store_true", help="禁用词级时间戳（默认开启词级对齐以消除长配乐导致的提前显示）")
    parser.add_argument("--keep-audio", action="store_true", help="保留中间转换生成的 16kHz WAV 文件")
    parser.add_argument("--output-srt", default=None, help="自定义输出的原声 SRT 文件路径（默认保存在媒体同目录下）")

    args = parser.parse_args()

    check_prerequisites()

    media_path = Path(args.media_path).resolve()
    if not media_path.is_file():
        print_err(f"找不到指定的媒体文件: {media_path}")
        sys.exit(1)

    media_dir = media_path.parent
    base_name = media_path.stem
    audio_wav = media_dir / f"{base_name}_audio_temp_{os.getpid()}.wav"

    lang_tag = args.source_lang.lower()
    target_raw_srt = Path(args.output_srt).resolve() if args.output_srt else media_dir / f"{base_name}.{lang_tag}.raw.srt"

    print("=" * 60)
    print(f"📂 输入媒体: {media_path.name}")
    meta = probe_media_streams(media_path)
    print(f"📋 媒体类型: {meta['media_type']}")
    if meta['duration'] > 0:
        minutes = int(meta['duration'] // 60)
        seconds = int(meta['duration'] % 60)
        print(f"⏱️ 媒体时长: {minutes} 分 {seconds} 秒 ({meta['duration']:.1f} 秒)")
    print(f"🌐 原始语言: {args.source_lang}")
    print(f"🧠 转录模型: {args.model}")
    print("=" * 60)

    try:
        # 1. 提取标准化音频流
        extract_wav_audio(media_path, audio_wav)

        # 2. 调用 Whisper 生成原生 SRT
        word_timestamps = not args.no_word_timestamps
        generated_srt = run_whisper_transcribe(audio_wav, media_dir, args.model, args.source_lang, word_timestamps)

        if not generated_srt.exists():
            print_err("Whisper 转录未正常生成 SRT 文件。")
            sys.exit(1)

        # 3. 将生成的 srt 重命名或移动为规范的目标文件
        if generated_srt != target_raw_srt:
            if target_raw_srt.exists():
                target_raw_srt.unlink()
            shutil.move(str(generated_srt), str(target_raw_srt))

        print("\n" + "=" * 60)
        print("✅ 原声 SRT 字幕提取完成！")
        print(f"📄 原声字幕路径: {target_raw_srt}")
        print("=" * 60)

        # 输出机器可读的标记行供调用端提取路径
        print(f"RAW_SRT_PATH: {target_raw_srt}")

    finally:
        cleanup_temp_files(audio_wav, args.keep_audio)


if __name__ == "__main__":
    main()
