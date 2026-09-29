"""
SRT Parser for AutoCapCut.
Handles parsing of SubRip (.srt) files with high tolerance for timestamp variations and formatting.
"""

import re
from typing import List, Dict, Any


def srt_timestamp_to_ms(t_str: str) -> int:
    """Convert SRT timestamp 'HH:MM:SS,mmm' or 'HH:MM:SS.mmm' to milliseconds."""
    t_str = t_str.strip().replace(',', '.')
    parts = t_str.split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid timestamp format: {t_str}")
    h = int(parts[0])
    m = int(parts[1])
    s_parts = parts[2].split('.')
    s = int(s_parts[0])
    ms = int(s_parts[1]) if len(s_parts) > 1 else 0
    # Handle varying precision for ms (e.g. 2 digits or 3 digits)
    if len(s_parts) > 1 and len(s_parts[1]) == 2:
        ms *= 10
    elif len(s_parts) > 1 and len(s_parts[1]) == 1:
        ms *= 100
    return (h * 3600 + m * 60 + s) * 1000 + ms


def clean_subtitle_text(text: str) -> str:
    """Remove HTML/formatting tags and clean whitespace."""
    # Remove HTML tags like <i>, <b>, <font ...>
    text = re.sub(r'<[^>]+>', '', text)
    # Remove ASS/SSA style tags {\an8}, etc.
    text = re.sub(r'\{[^}]+\}', '', text)
    # Collapse multiple whitespace
    text = ' '.join(text.strip().split())
    return text


def normalize_words_for_matching(text: str) -> str:
    """Normalize text for text matching: lowercase, strip punctuation."""
    text = text.lower()
    # Replace em-dash, en-dash, hyphens with space
    text = re.sub(r'[\u2010-\u2015—–-]', ' ', text)
    # Remove all punctuation except alphanumeric and unicode word characters
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())


def parse_srt(srt_path: str) -> List[Dict[str, Any]]:
    """
    Parse an SRT file into a list of subtitle dictionaries.
    
    Each item contains:
    - index: int
    - start_ms: int
    - end_ms: int
    - duration_ms: int
    - text: str (cleaned human-readable text)
    - words: List[str] (normalized words for sequence alignment)
    """
    with open(srt_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read()

    # Pattern matches:
    # 1. subtitle index
    # 2. start timestamp
    # 3. end timestamp
    # 4. text content until next subtitle or EOF
    pattern = re.compile(
        r'(\d+)\s*\r?\n(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*\r?\n(.*?)(?=\r?\n\s*\r?\n\d+\s*\r?\n|\Z)',
        re.DOTALL
    )

    matches = pattern.findall(content)
    subtitles = []

    for idx_str, start_str, end_str, raw_text in matches:
        clean_txt = clean_subtitle_text(raw_text)
        if not clean_txt:
            continue
        try:
            start_ms = srt_timestamp_to_ms(start_str)
            end_ms = srt_timestamp_to_ms(end_str)
            norm_words = normalize_words_for_matching(clean_txt).split()
            subtitles.append({
                'index': int(idx_str),
                'start_ms': start_ms,
                'end_ms': end_ms,
                'duration_ms': max(0, end_ms - start_ms),
                'text': clean_txt,
                'words': norm_words
            })
        except Exception:
            continue

    return subtitles
