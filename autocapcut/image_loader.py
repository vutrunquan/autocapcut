"""
Media Loader for AutoCapCut.
Scans media directories (images and video clips) and sorts according to chosen sorting mode:
- 'abc': Natural alphanumeric order (1, 2, 10, 001, 002...)
- 'oldest_first': Creation/Modified time from Oldest to Newest
- 'newest_first': Creation/Modified time from Newest to Oldest
"""

import os
import sys
import re
import time
import json
import subprocess
from typing import List, Tuple, Optional, Callable
from PIL import Image, ImageFilter


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.webm'}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def extract_numerical_key(filename: str) -> Tuple[int, str]:
    """
    Extract the first continuous integer found in the filename for natural sorting.
    Returns (number, original_filename_lowercase).
    """
    base_name = os.path.splitext(filename)[0]
    match = re.search(r'\d+', base_name)
    if match:
        return (int(match.group()), filename.lower())
    return (float('inf'), filename.lower())


def load_sorted_media(folder_path: str, sort_mode: str = 'abc') -> List[str]:
    """
    Scan a directory for media files (images and video clips) and sort according to sort_mode.
    
    Args:
        folder_path: Path to folder containing media
        sort_mode: 'abc' | 'oldest_first' | 'newest_first'
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Thư mục media không tồn tại: {folder_path}")

    files = os.listdir(folder_path)
    media_files = [
        f for f in files
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
    ]

    if not media_files:
        raise ValueError(f"Không tìm thấy file ảnh hoặc video hợp lệ nào trong: {folder_path}")

    full_paths = [os.path.join(folder_path, f) for f in media_files]

    if sort_mode == 'oldest_first':
        full_paths.sort(key=lambda p: os.path.getmtime(p))
    elif sort_mode == 'newest_first':
        full_paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    else:
        # Default 'abc': natural numerical sorting
        full_paths.sort(key=lambda p: extract_numerical_key(os.path.basename(p)))

    return full_paths


# Backward compatibility alias
def load_sorted_images(folder_path: str, sort_mode: str = 'abc') -> List[str]:
    return load_sorted_media(folder_path, sort_mode)


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get (width, height) of an image without loading full image into memory."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (1920, 1080)


def get_watermark_remover_script() -> Optional[str]:
    """Locate the batch_remover.mjs script in tools/gemini-watermark-remover."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, 'tools', 'gemini-watermark-remover', 'batch_remover.mjs')
    if os.path.exists(script_path):
        return script_path
    return None


def remove_gemini_watermark_from_image(image_path: str, output_cache_dir: str) -> str:
    """
    Remove Gemini spark watermark using Reverse Alpha Blending (GargantuaX/gemini-watermark-remover).
    Creates a mathematically exact clean copy in output_cache_dir and returns the new image path.
    """
    try:
        os.makedirs(output_cache_dir, exist_ok=True)
        filename = os.path.basename(image_path)
        cached_path = os.path.join(output_cache_dir, f"clean_{filename}")

        if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
            return cached_path

        tool_script = get_watermark_remover_script()
        if tool_script and os.path.exists(tool_script):
            cmd = ['node', tool_script, '--single', image_path, cached_path]
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            res = subprocess.run(cmd, capture_output=True, text=True, creationflags=creationflags)
            if res.returncode == 0 and os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
                return cached_path
    except Exception:
        pass
    return image_path


def batch_remove_gemini_watermarks(
    image_paths: List[str],
    output_cache_dir: str,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    overwrite: bool = True
) -> List[str]:
    """
    Batch remove Gemini watermarks from multiple images using Reverse Alpha Blending.
    Runs multi-threaded concurrency in Node.js for blazing fast performance.
    """
    os.makedirs(output_cache_dir, exist_ok=True)
    tool_script = get_watermark_remover_script()
    if not tool_script or not os.path.exists(tool_script):
        return image_paths

    tasks = []
    cleaned_paths = []

    for p in image_paths:
        ext = os.path.splitext(p)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}:
            out_p = os.path.join(output_cache_dir, f"clean_{os.path.basename(p)}")
            cleaned_paths.append(out_p)
            if overwrite or not os.path.exists(out_p) or os.path.getsize(out_p) == 0:
                tasks.append({'input': p, 'output': out_p, 'overwrite': overwrite})
        else:
            cleaned_paths.append(p)

    if not tasks:
        # All already cached or non-images
        return [c if os.path.exists(c) else orig for orig, c in zip(image_paths, cleaned_paths)]

    tasks_json_file = os.path.join(output_cache_dir, f"_tasks_{int(time.time()*1000)}.json")
    try:
        with open(tasks_json_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f)

        creationflags = 0
        if sys.platform == 'win32':
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

        cmd = ['node', tool_script]
        if overwrite:
            cmd.append('--overwrite')
        cmd.extend(['--batch', tasks_json_file])

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=creationflags
        )

        total_tasks = len(tasks)
        processed = 0

        if proc.stdout:
            for line in proc.stdout:
                line_str = line.strip()
                if line_str.startswith('[PROGRESS]'):
                    processed += 1
                    pct = processed / total_tasks
                    if progress_callback:
                        progress_callback(f"Xóa watermark ({processed}/{total_tasks})", pct)

        proc.wait()
    except Exception:
        pass
    finally:
        if os.path.exists(tasks_json_file):
            try:
                os.remove(tasks_json_file)
            except Exception:
                pass

    final_paths = []
    for orig, cleaned in zip(image_paths, cleaned_paths):
        if os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            final_paths.append(cleaned)
        else:
            final_paths.append(orig)

    return final_paths
