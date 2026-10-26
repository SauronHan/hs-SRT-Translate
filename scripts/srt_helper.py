#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
srt_helper.py
SRT 字幕实用辅助工具套件。
功能包含：
1. 提取纯文本背景语料（用于 Agent 理解视频全局背景与提炼术语表）
2. 长 SRT 分块（Chunking，防大模型单次生成截断）
3. 翻译后分块合并（Merging）
4. 原始与翻译 SRT 严格时间戳及条目 1:1 对齐校验（Validation）
5. 源语言与目标语言双语字幕合成（Bilingual SRT Generation）
完全采用 Python 标准库实现，跨平台兼容。
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import List, Tuple


@dataclass
class SubtitleItem:
    index: int
    start_time: str
    end_time: str
    text: str

    def to_srt_block(self) -> str:
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text.strip()}\n"


def parse_srt(content: str) -> List[SubtitleItem]:
    """解析 SRT 文本内容为结构化 SubtitleItem 列表，具备良好的容错性。"""
    # 统一换行符
    content = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not content:
        return []

    # 按连续双换行或多换行切分
    raw_blocks = re.split(r"\n\s*\n", content)
    items: List[SubtitleItem] = []

    time_pattern = re.compile(r"^(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})")

    for block in raw_blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        # 尝试匹配时间行
        time_line_idx = -1
        time_match = None
        for i, line in enumerate(lines):
            m = time_pattern.match(line)
            if m:
                time_line_idx = i
                time_match = m
                break

        if time_line_idx != -1 and time_match:
            # 获取序号
            try:
                idx = int(lines[0]) if time_line_idx > 0 else (len(items) + 1)
            except ValueError:
                idx = len(items) + 1

            start_time = time_match.group(1).replace(".", ",")
            end_time = time_match.group(2).replace(".", ",")
            text = "\n".join(lines[time_line_idx + 1:])
            items.append(SubtitleItem(index=idx, start_time=start_time, end_time=end_time, text=text))

    return items


def dump_srt(items: List[SubtitleItem]) -> str:
    """将 SubtitleItem 列表渲染为标准 SRT 字符串。"""
    blocks = []
    for i, item in enumerate(items, 1):
        blocks.append(f"{i}\n{item.start_time} --> {item.end_time}\n{item.text.strip()}")
    return "\n\n".join(blocks) + "\n"


def extract_context_text(items: List[SubtitleItem]) -> str:
    """提取适合大模型阅读与理解的带稀疏时间标记的纯文本流。"""
    lines = []
    for item in items:
        # 提取 MM:SS 紧凑时间戳
        start_parts = item.start_time.split(":")
        if len(start_parts) >= 3:
            hh, mm, ss_ms = start_parts[0], start_parts[1], start_parts[2]
            ss = ss_ms.split(",")[0]
            total_m = int(hh) * 60 + int(mm)
            stamp = f"{total_m:02d}:{ss}" if total_m > 0 else f"{mm}:{ss}"
        else:
            stamp = item.start_time
        lines.append(f"[{stamp}] {item.text}")
    return "\n".join(lines)


def split_srt_into_chunks(items: List[SubtitleItem], chunk_size: int = 60) -> List[List[SubtitleItem]]:
    """按指定组数将字幕划分为批次。"""
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    return chunks


def validate_subtitles(original_items: List[SubtitleItem], translated_items: List[SubtitleItem]) -> Tuple[bool, List[str]]:
    """校验翻译后字幕与原始字幕的条目数和时间戳是否严格对齐。"""
    errors = []
    if len(original_items) != len(translated_items):
        errors.append(f"条目总数不匹配: 原始字幕包含 {len(original_items)} 条，翻译字幕包含 {len(translated_items)} 条。")

    min_len = min(len(original_items), len(translated_items))
    for i in range(min_len):
        orig = original_items[i]
        trans = translated_items[i]

        if orig.start_time != trans.start_time or orig.end_time != trans.end_time:
            errors.append(
                f"第 {i+1} 条时间戳错位: 原始 [{orig.start_time} --> {orig.end_time}] vs 翻译 [{trans.start_time} --> {trans.end_time}]"
            )
        if not trans.text.strip():
            errors.append(f"第 {i+1} 条翻译内容为空。")

        if len(errors) > 10:
            errors.append("...（已发现超过 10 处错误，停止后续检查）")
            break

    is_valid = len(errors) == 0
    return is_valid, errors


def build_bilingual_subtitles(
    src_items: List[SubtitleItem],
    tgt_items: List[SubtitleItem],
    target_first: bool = True
) -> List[SubtitleItem]:
    """合成双语字幕列表。target_first=True 表示上方显示目标语言（译文），下方显示源语言（原文）。"""
    bilingual_items: List[SubtitleItem] = []
    total = min(len(src_items), len(tgt_items))

    for i in range(total):
        src = src_items[i]
        tgt = tgt_items[i]
        if target_first:
            combined_text = f"{tgt.text.strip()}\n{src.text.strip()}"
        else:
            combined_text = f"{src.text.strip()}\n{tgt.text.strip()}"

        bilingual_items.append(
            SubtitleItem(
                index=i + 1,
                start_time=src.start_time,
                end_time=src.end_time,
                text=combined_text
            )
        )
    return bilingual_items


def main():
    parser = argparse.ArgumentParser(description="SRT 字幕辅助工具箱")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. extract-text
    p_text = subparsers.add_parser("extract-text", help="从 SRT 中提取纯文本背景语料，供 Agent 快速通读")
    p_text.add_argument("srt_path", help="输入 SRT 文件路径")
    p_text.add_argument("--output", "-o", default=None, help="输出 TXT 文件路径（默认同名 .context.txt）")

    # 2. split
    p_split = subparsers.add_parser("split", help="将长 SRT 按批次切分为若干子文件")
    p_split.add_argument("srt_path", help="输入 SRT 文件路径")
    p_split.add_argument("--chunk-size", "-s", type=int, default=60, help="每批包含的字幕组数（默认 60）")
    p_split.add_argument("--output-dir", "-o", default=None, help="切分文件存放目录（默认同级 _chunks 目录）")

    # 3. validate
    p_val = subparsers.add_parser("validate", help="校验翻译后 SRT 与原 SRT 的时间轴与条目对齐情况")
    p_val.add_argument("orig_srt", help="原始 SRT 文件路径")
    p_val.add_argument("trans_srt", help="翻译后的 SRT 文件路径")

    # 4. bilingual
    p_bi = subparsers.add_parser("bilingual", help="合成双语对照 SRT 字幕文件")
    p_bi.add_argument("src_srt", help="源语言 SRT 文件路径")
    p_bi.add_argument("tgt_srt", help="目标语言 SRT 文件路径")
    p_bi.add_argument("--output", "-o", required=True, help="输出的双语 SRT 文件路径")
    p_bi.add_argument("--source-first", action="store_true", help="设为原文在上、译文在下（默认是译文在上、原文在下）")

    args = parser.parse_args()

    if args.command == "extract-text":
        srt_file = Path(args.srt_path).resolve()
        if not srt_file.is_file():
            print(f"[错误] 文件不存在: {srt_file}", file=sys.stderr)
            sys.exit(1)
        items = parse_srt(srt_file.read_text(encoding="utf-8", errors="ignore"))
        txt = extract_context_text(items)
        out_path = Path(args.output).resolve() if args.output else srt_file.parent / f"{srt_file.stem}.context.txt"
        out_path.write_text(txt, encoding="utf-8")
        print(f"✅ 纯文本背景语料提取成功: {out_path} (共 {len(items)} 条字幕)")

    elif args.command == "split":
        srt_file = Path(args.srt_path).resolve()
        if not srt_file.is_file():
            print(f"[错误] 文件不存在: {srt_file}", file=sys.stderr)
            sys.exit(1)
        items = parse_srt(srt_file.read_text(encoding="utf-8", errors="ignore"))
        chunks = split_srt_into_chunks(items, args.chunk_size)
        out_dir = Path(args.output_dir).resolve() if args.output_dir else srt_file.parent / f"{srt_file.stem}_chunks"
        out_dir.mkdir(parents=True, exist_ok=True)

        for idx, chunk in enumerate(chunks, 1):
            chunk_file = out_dir / f"chunk_{idx:03d}.srt"
            chunk_file.write_text(dump_srt(chunk), encoding="utf-8")

        print(f"✅ 成功将 {len(items)} 条字幕切分为 {len(chunks)} 个分块，存放于: {out_dir}")

    elif args.command == "validate":
        orig_file = Path(args.orig_srt).resolve()
        trans_file = Path(args.trans_srt).resolve()
        if not orig_file.is_file() or not trans_file.is_file():
            print("[错误] 指定的文件不存在", file=sys.stderr)
            sys.exit(1)

        orig_items = parse_srt(orig_file.read_text(encoding="utf-8", errors="ignore"))
        trans_items = parse_srt(trans_file.read_text(encoding="utf-8", errors="ignore"))

        valid, errors = validate_subtitles(orig_items, trans_items)
        if valid:
            print(f"✅ 校验通过！原始与翻译字幕完全 1:1 对齐（共 {len(orig_items)} 条）。")
        else:
            print("❌ 校验未通过，发现对齐问题：", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "bilingual":
        src_file = Path(args.src_srt).resolve()
        tgt_file = Path(args.tgt_srt).resolve()
        if not src_file.is_file() or not tgt_file.is_file():
            print("[错误] 指定的文件不存在", file=sys.stderr)
            sys.exit(1)

        src_items = parse_srt(src_file.read_text(encoding="utf-8", errors="ignore"))
        tgt_items = parse_srt(tgt_file.read_text(encoding="utf-8", errors="ignore"))

        target_first = not args.source_first
        bi_items = build_bilingual_subtitles(src_items, tgt_items, target_first=target_first)
        out_file = Path(args.output).resolve()
        out_file.write_text(dump_srt(bi_items), encoding="utf-8")
        print(f"✅ 双语对照字幕合成成功: {out_file} (共 {len(bi_items)} 条字幕)")


if __name__ == "__main__":
    main()
