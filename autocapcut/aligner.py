"""
Aligner for AutoCapCut.
Performs high-precision alignment between scene script lines and SRT subtitle timestamps.
"""

import difflib
import re
from typing import List, Dict, Any, Optional
from .srt_parser import normalize_words_for_matching


def read_script_lines(script_path: str) -> List[str]:
    """
    Read script file where each non-empty line represents one scene / image.
    Supports UTF-8, UTF-8-SIG, and fallback encodings.
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'latin-1']
    content = None
    for enc in encodings:
        try:
            with open(script_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, Exception):
            continue

    if content is None:
        raise ValueError(f"Không thể đọc file kịch bản: {script_path}")

    # Split lines and remove empty/whitespace-only lines
    raw_lines = content.splitlines()
    cleaned_lines = [line.strip() for line in raw_lines if line.strip()]
    if not cleaned_lines:
        raise ValueError("File kịch bản rỗng hoặc không có dòng nội dung nào!")
    return cleaned_lines


def align_scenes_with_srt(
    script_lines: List[str],
    srt_subtitles: List[Dict[str, Any]],
    total_audio_ms: int,
    lead_in_ms: int = 0
) -> List[Dict[str, Any]]:
    """
    Align each script line to timestamps derived from SRT subtitles.
    
    Guarantees:
    - Exactly len(script_lines) output scenes.
    - Continuous timeline: scene 0 starts at 0ms; each subsequent scene starts
      immediately where the previous scene ends (no black frame gaps!).
    - Final scene extends to total_audio_ms (or last spoken word).
    - Every scene has duration >= 300ms.
    """
    if not script_lines:
        return []

    # 1. Flatten all SRT words with estimated timestamps
    flat_srt_words = []
    for s_idx, s in enumerate(srt_subtitles):
        words = s['words']
        n_words = len(words)
        dur = max(0, s['end_ms'] - s['start_ms'])
        for w_idx, w in enumerate(words):
            w_start = s['start_ms'] + int(dur * (w_idx / max(1, n_words)))
            w_end = s['start_ms'] + int(dur * ((w_idx + 1) / max(1, n_words)))
            flat_srt_words.append({
                'word': w,
                'sub_idx': s_idx,
                'start_ms': w_start,
                'end_ms': w_end
            })

    if not flat_srt_words:
        # Fallback if SRT had no words: evenly divide audio duration
        n = len(script_lines)
        per_scene = max(1000, total_audio_ms // max(1, n))
        scenes = []
        for i, line in enumerate(script_lines):
            st = i * per_scene
            en = total_audio_ms if i == n - 1 else (i + 1) * per_scene
            scenes.append({
                'scene_idx': i,
                'text': line,
                'start_ms': st,
                'end_ms': en,
                'duration_ms': max(300, en - st)
            })
        return scenes

    # 2. Tokenize each script line and build flat list with scene indices
    script_words = []
    script_word_scene_idx = []
    for s_i, line in enumerate(script_lines):
        norm_line = normalize_words_for_matching(line)
        w_list = norm_line.split()
        if not w_list:
            w_list = ['...']
        for w in w_list:
            script_words.append(w)
            script_word_scene_idx.append(s_i)

    # 3. Global sequence alignment using SequenceMatcher
    sm = difflib.SequenceMatcher(
        None,
        [x['word'] for x in flat_srt_words],
        script_words
    )

    script_to_srt = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for offset in range(i2 - i1):
                script_to_srt[j1 + offset] = i1 + offset
        elif tag == 'replace':
            len_j = j2 - j1
            len_i = i2 - i1
            for k in range(len_j):
                mapped_i = min(len(flat_srt_words) - 1, i1 + int(k * len_i / max(1, len_j)))
                script_to_srt[j1 + k] = mapped_i
        elif tag == 'insert':
            for k in range(j2 - j1):
                script_to_srt[j1 + k] = min(len(flat_srt_words) - 1, i1)

    # 4. Extract raw speech bounds for each scene
    raw_bounds = []
    last_known_srt_idx = 0
    for s_i in range(len(script_lines)):
        w_idxs = [idx for idx, sc in enumerate(script_word_scene_idx) if sc == s_i]
        matched_srt_indices = [script_to_srt[w] for w in w_idxs if w in script_to_srt]

        if matched_srt_indices:
            min_srt = min(matched_srt_indices)
            max_srt = max(matched_srt_indices)
            last_known_srt_idx = max_srt
            st = flat_srt_words[min_srt]['start_ms']
            en = flat_srt_words[max_srt]['end_ms']
        else:
            # If no words matched this line, estimate from last known position
            st = flat_srt_words[last_known_srt_idx]['end_ms']
            en = st + 1500

        raw_bounds.append({'scene_idx': s_i, 'raw_start': st, 'raw_end': en})

    # 5. Form continuous, gapless scene cuts
    final_scenes = []
    n = len(raw_bounds)
    for i in range(n):
        if i == 0:
            start_ms = 0
        else:
            start_ms = final_scenes[i - 1]['end_ms']

        if i < n - 1:
            next_raw_start = raw_bounds[i + 1]['raw_start'] - lead_in_ms
            # Cut at next scene's speech onset, ensuring minimum duration
            end_ms = max(start_ms + 300, next_raw_start)
        else:
            # Last scene spans to the end of the audio
            end_ms = max(start_ms + 300, total_audio_ms)

        final_scenes.append({
            'scene_idx': i,
            'text': script_lines[i],
            'start_ms': start_ms,
            'end_ms': end_ms,
            'duration_ms': max(300, end_ms - start_ms),
            'start_us': start_ms * 1000,
            'duration_us': (end_ms - start_ms) * 1000
        })

    return final_scenes
