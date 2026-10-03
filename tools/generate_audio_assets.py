"""
Studio Audio Asset Synthesizer for AutoCapCut.
Generates high-definition, royalty-free audio files for:
- CapCut-style SFX (Whooshes, Swooshes, Camera Shutter, Clicks, Kaching, Impact Boom, Pop, Ding, Glitch, etc.)
- CapCut-style BGM Presets (Cinematic, News/Finance, Lofi Chill, Dramatic Suspense, Happy Vlog)
All files are saved as clean 16-bit 44.1kHz Stereo WAV files.
"""

import os
import sys
import wave
import struct
import math
import numpy as np
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SAMPLE_RATE = 44100

BASE_DIR = Path(__file__).resolve().parent.parent
SFX_DIR = BASE_DIR / "assets" / "sfx"
BGM_DIR = BASE_DIR / "assets" / "bgm"

SFX_DIR.mkdir(parents=True, exist_ok=True)
BGM_DIR.mkdir(parents=True, exist_ok=True)


def save_stereo_wav(filepath: Path, left_ch: np.ndarray, right_ch: np.ndarray):
    """Normalize and write stereo 16-bit PCM WAV with 1.0s trailing silence safety buffer."""
    peak = max(np.max(np.abs(left_ch)), np.max(np.abs(right_ch)), 1e-6)
    if peak > 0.98:
        left_ch = (left_ch / peak) * 0.95
        right_ch = (right_ch / peak) * 0.95

    # Append 1.0s clean digital silence buffer to prevent CapCut timeline frame quantization EOF errors
    silence_len = int(SAMPLE_RATE * 1.0)
    left_ch = np.pad(left_ch, (0, silence_len), 'constant')
    right_ch = np.pad(right_ch, (0, silence_len), 'constant')

    left_int16 = np.int16(np.clip(left_ch, -1.0, 1.0) * 32767)
    right_int16 = np.int16(np.clip(right_ch, -1.0, 1.0) * 32767)
    interleaved = np.empty((len(left_int16) * 2,), dtype=np.int16)
    interleaved[0::2] = left_int16
    interleaved[1::2] = right_int16

    with wave.open(str(filepath), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(interleaved.tobytes())


# ==============================================================================
# 1. SFX GENERATORS
# ==============================================================================

def make_whoosh_cinematic_deep(filepath: Path):
    """Deep, cinematic sub-bass whoosh transition."""
    dur = 0.85
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    # Pitch curve: rises to peak at 60% then swooshes down
    f_curve = 80 + 350 * np.exp(-((t - 0.50 * dur) ** 2) / 0.03)
    phase = 2 * np.pi * np.cumsum(f_curve) / SAMPLE_RATE

    env = np.exp(-((t - 0.48 * dur) ** 2) / 0.035)
    noise = np.random.normal(0, 0.4, len(t))
    # Low-pass filter approximation on noise
    kernel_size = 45
    noise_smooth = np.convolve(noise, np.ones(kernel_size)/kernel_size, mode='same')

    sub_bass = np.sin(phase) * 0.6
    body = (sub_bass + noise_smooth * 0.9) * env

    # Stereo pan sweep left to right
    pan = (t / dur)
    left = body * (1.0 - 0.7 * pan)
    right = body * (0.3 + 0.7 * pan)
    save_stereo_wav(filepath, left, right)


def make_whoosh_fast(filepath: Path):
    """Fast, crisp whoosh (0.35s)."""
    dur = 0.38
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-((t - 0.18) ** 2) / 0.009)
    noise = np.random.normal(0, 0.5, len(t))
    k = 20
    noise_smooth = np.convolve(noise, np.ones(k)/k, mode='same')
    sweep = np.sin(2 * np.pi * (200 + 1200 * (t / dur)) * t) * 0.25
    body = (noise_smooth + sweep) * env
    pan = t / dur
    save_stereo_wav(filepath, body * (1 - 0.8*pan), body * (0.2 + 0.8*pan))


def make_whoosh_soft_air(filepath: Path):
    """Soft airy wind whoosh (0.6s)."""
    dur = 0.60
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-((t - 0.30) ** 2) / 0.025)
    noise = np.random.normal(0, 0.35, len(t))
    k = 35
    filtered_noise = np.convolve(noise, np.hanning(k)/np.sum(np.hanning(k)), mode='same')
    body = filtered_noise * env
    save_stereo_wav(filepath, body * 0.85, body * 0.95)


def make_whoosh_heavy_bass(filepath: Path):
    """Heavy bass rumble impact whoosh (1.1s)."""
    dur = 1.10
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-((t - 0.40) ** 2) / 0.06)
    sub = np.sin(2 * np.pi * (50 + 60 * np.exp(-t * 2)) * t) * 0.7
    noise = np.random.normal(0, 0.4, len(t))
    k = 50
    noise_filt = np.convolve(noise, np.ones(k)/k, mode='same')
    body = (sub + noise_filt * 0.6) * env
    save_stereo_wav(filepath, body, body)


def make_swoosh_fast_whip(filepath: Path):
    """Fast whip swoosh (0.25s)."""
    dur = 0.28
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-((t - 0.12) ** 2) / 0.005)
    f = 350 + 2200 * np.exp(-((t - 0.12) ** 2) / 0.01)
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    body = (np.sin(phase) * 0.4 + np.random.normal(0, 0.3, len(t))) * env
    save_stereo_wav(filepath, body * 0.9, body * 0.6)


def make_swoosh_slide(filepath: Path):
    """Smooth paper/UI slide swoosh (0.35s)."""
    dur = 0.35
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.sin(np.pi * (t / dur)) ** 1.8
    noise = np.random.normal(0, 0.4, len(t))
    k = 18
    body = np.convolve(noise, np.ones(k)/k, mode='same') * env
    save_stereo_wav(filepath, body * 0.7, body * 0.85)


def make_camera_shutter(filepath: Path):
    """Realistic DSLR camera shutter click + clack (0.28s)."""
    dur = 0.32
    n = int(SAMPLE_RATE * dur)
    left = np.zeros(n)
    right = np.zeros(n)

    # 1. First click at t=0.01s (Mirror up click)
    t_c1 = np.linspace(0, 0.035, int(SAMPLE_RATE * 0.035), endpoint=False)
    env1 = np.exp(-t_c1 * 180)
    c1 = (np.sin(2 * np.pi * 3200 * t_c1) * 0.6 + np.sin(2 * np.pi * 1800 * t_c1) * 0.4 + np.random.normal(0, 0.5, len(t_c1))) * env1
    idx1 = int(SAMPLE_RATE * 0.01)
    left[idx1:idx1+len(c1)] += c1 * 0.9
    right[idx1:idx1+len(c1)] += c1 * 0.85

    # 2. Second mechanical clack at t=0.08s (Curtain shutter)
    t_c2 = np.linspace(0, 0.065, int(SAMPLE_RATE * 0.065), endpoint=False)
    env2 = np.exp(-t_c2 * 90)
    c2 = (np.sin(2 * np.pi * 1250 * t_c2) * 0.8 + np.sin(2 * np.pi * 850 * t_c2) * 0.5 + np.random.normal(0, 0.6, len(t_c2))) * env2
    idx2 = int(SAMPLE_RATE * 0.08)
    left[idx2:idx2+len(c2)] += c2 * 0.95
    right[idx2:idx2+len(c2)] += c2 * 1.0

    save_stereo_wav(filepath, left, right)


def make_mouse_click(filepath: Path):
    """Crisp PC mouse click sound (0.12s)."""
    dur = 0.12
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, 0.04, int(SAMPLE_RATE * 0.04), endpoint=False)
    env = np.exp(-t * 300)
    click = (np.sin(2 * np.pi * 2600 * t) * 0.7 + np.sin(2 * np.pi * 4200 * t) * 0.4 + np.random.normal(0, 0.4, len(t))) * env
    out = np.zeros(n)
    idx = int(SAMPLE_RATE * 0.01)
    out[idx:idx+len(click)] = click
    save_stereo_wav(filepath, out * 0.95, out * 0.85)


def make_keyboard_typing(filepath: Path):
    """Mechanical keyboard key clack (0.16s)."""
    dur = 0.16
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, 0.06, int(SAMPLE_RATE * 0.06), endpoint=False)
    env = np.exp(-t * 140)
    clack = (np.sin(2 * np.pi * 1450 * t) * 0.6 + np.sin(2 * np.pi * 820 * t) * 0.5 + np.random.normal(0, 0.45, len(t))) * env
    out = np.zeros(n)
    idx = int(SAMPLE_RATE * 0.01)
    out[idx:idx+len(clack)] = clack
    save_stereo_wav(filepath, out * 0.9, out * 0.95)


def make_bubble_pop(filepath: Path):
    """Clean bubble pop sound (0.15s)."""
    dur = 0.15
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-t * 55)
    f = 1100 * np.exp(-t * 30) + 200
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    body = np.sin(phase) * env
    save_stereo_wav(filepath, body, body)


def make_cash_register_kaching(filepath: Path):
    """Iconic cash register / Kaching sound (1.1s)."""
    dur = 1.10
    n = int(SAMPLE_RATE * dur)
    left = np.zeros(n)
    right = np.zeros(n)

    # 1. Cash drawer latch slide (0.0s to 0.12s)
    t_sl = np.linspace(0, 0.12, int(SAMPLE_RATE * 0.12), endpoint=False)
    env_sl = np.sin(np.pi * (t_sl / 0.12))
    slide = np.random.normal(0, 0.35, len(t_sl)) * env_sl
    left[:len(slide)] += slide * 0.6
    right[:len(slide)] += slide * 0.7

    # 2. Bright double chime bell (t=0.10s)
    t_ch = np.linspace(0, 0.95, int(SAMPLE_RATE * 0.95), endpoint=False)
    env_ch = np.exp(-t_ch * 5.5)
    bell1 = np.sin(2 * np.pi * 2093.0 * t_ch) * 0.6  # C7
    bell2 = np.sin(2 * np.pi * 2637.0 * t_ch) * 0.45 # E7
    bell3 = np.sin(2 * np.pi * 3135.9 * t_ch) * 0.3  # G7
    shimmer = (bell1 + bell2 + bell3) * env_ch

    idx_ch = int(SAMPLE_RATE * 0.10)
    left[idx_ch:idx_ch+len(shimmer)] += shimmer * 0.95
    right[idx_ch:idx_ch+len(shimmer)] += shimmer * 0.85

    save_stereo_wav(filepath, left, right)


def make_cinematic_boom_impact(filepath: Path):
    """Epic cinematic hit/boom impact (1.6s)."""
    dur = 1.60
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-t * 3.5)
    f = 75 * np.exp(-t * 4) + 38
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    sub = np.sin(phase) * 0.8
    noise = np.random.normal(0, 0.5, len(t)) * np.exp(-t * 22)
    body = (sub + noise) * env
    save_stereo_wav(filepath, body, body)


def make_bell_ding_chime(filepath: Path):
    """Bright bell ding notification chime (1.2s)."""
    dur = 1.20
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-t * 4.2)
    chime = (
        np.sin(2 * np.pi * 1760.0 * t) * 0.65 +  # A6
        np.sin(2 * np.pi * 2637.0 * t) * 0.35 +  # E7
        np.sin(2 * np.pi * 3520.0 * t) * 0.20     # A7
    ) * env
    save_stereo_wav(filepath, chime * 0.9, chime)


def make_tape_rewind(filepath: Path):
    """Cassette tape rewind effect (0.75s)."""
    dur = 0.75
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.sin(np.pi * (t / dur)) ** 1.5
    f = 400 + 3200 * (t / dur) ** 2
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    buzz = np.sin(phase) * np.sin(2 * np.pi * 60 * t) * 0.5
    noise = np.random.normal(0, 0.3, len(t))
    body = (buzz + noise * 0.4) * env
    save_stereo_wav(filepath, body * 0.85, body)


def make_glitch_digital(filepath: Path):
    """Digital tech glitch stutter (0.35s)."""
    dur = 0.35
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    env = np.exp(-t * 12)
    carrier = np.sin(2 * np.pi * 880 * t)
    mod = np.sin(2 * np.pi * 110 * t)
    stutter = np.sign(np.sin(2 * np.pi * 32 * t))
    body = (carrier * mod * stutter * 0.6 + np.random.normal(0, 0.3, len(t))) * env
    save_stereo_wav(filepath, body * 0.9, body * 0.75)


# ==============================================================================
# 2. BGM PRESET GENERATORS (High-Quality Loopable Stereo Tracks ~30s each)
# ==============================================================================

def make_bgm_cinematic(filepath: Path):
    """
    Cinematic Piano & Soft Strings (32s loopable).
    Chords: Am - F - C - G (8 bars, 75 BPM).
    """
    bpm = 75
    bar_dur = (60.0 / bpm) * 4  # 3.2s per bar
    total_bars = 10
    dur = bar_dur * total_bars   # 32.0s
    n_samples = int(SAMPLE_RATE * dur)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    # Chord progression frequencies (Root, 3rd, 5th, Octave)
    # Am: A2 (110), C3 (130.8), E3 (164.8), A3 (220)
    # F:  F2 (87.3), A2 (110),   C3 (130.8), F3 (174.6)
    # C:  C2 (65.4), G2 (98.0),  C3 (130.8), E3 (164.8)
    # G:  G2 (98.0), B2 (123.5), D3 (146.8), G3 (196.0)
    prog = [
        [110.0, 130.81, 164.81, 220.0, 329.63, 440.0],  # Am
        [87.31, 110.0, 130.81, 174.61, 261.63, 349.23],  # F
        [65.41, 97.99, 130.81, 164.81, 261.63, 329.63],  # C
        [97.99, 123.47, 146.83, 196.0, 293.66, 392.0],   # G
    ]

    for bar in range(total_bars):
        c_idx = bar % 4
        notes = prog[c_idx]
        bar_start_s = bar * bar_dur

        # Soft String Pad for the full bar
        t_pad = np.linspace(0, bar_dur + 0.5, int(SAMPLE_RATE * (bar_dur + 0.5)), endpoint=False)
        pad_env = np.sin(np.pi * (t_pad / (bar_dur + 0.5))) ** 1.2
        pad_sound = np.zeros(len(t_pad))
        for freq in notes[:3]:
            pad_sound += np.sin(2 * np.pi * freq * t_pad) * 0.12
            pad_sound += np.sin(2 * np.pi * (freq * 2.01) * t_pad) * 0.05
        pad_sound *= pad_env

        s_idx = int(SAMPLE_RATE * bar_start_s)
        e_idx = min(n_samples, s_idx + len(pad_sound))
        left[s_idx:e_idx] += pad_sound[:e_idx-s_idx] * 0.65
        right[s_idx:e_idx] += pad_sound[:e_idx-s_idx] * 0.70

        # Gentle Piano Arpeggio (4 notes per bar)
        for beat in range(4):
            t_note = beat * (bar_dur / 4.0)
            note_freq = notes[(beat * 2) % len(notes)]
            t_p = np.linspace(0, 1.8, int(SAMPLE_RATE * 1.8), endpoint=False)
            p_env = np.exp(-t_p * 2.8)
            # Piano harmonics
            piano = (
                np.sin(2 * np.pi * note_freq * t_p) * 0.28 +
                np.sin(2 * np.pi * (note_freq * 2) * t_p) * 0.14 +
                np.sin(2 * np.pi * (note_freq * 3) * t_p) * 0.06
            ) * p_env

            pn_idx = int(SAMPLE_RATE * (bar_start_s + t_note))
            pn_end = min(n_samples, pn_idx + len(piano))
            # Slight stereo panning for arpeggio
            pan_l = 0.8 if beat % 2 == 0 else 0.4
            pan_r = 0.4 if beat % 2 == 0 else 0.8
            left[pn_idx:pn_end] += piano[:pn_end-pn_idx] * pan_l
            right[pn_idx:pn_end] += piano[:pn_end-pn_idx] * pan_r

    save_stereo_wav(filepath, left, right)


def make_bgm_news_tech(filepath: Path):
    """
    Modern News & Financial Tech Track (30s loopable, 120 BPM).
    Crisp bass pulse + tech synth pattern.
    """
    bpm = 120
    beat_dur = 60.0 / bpm  # 0.5s
    total_beats = 60       # 30.0s
    dur = beat_dur * total_beats
    n_samples = int(SAMPLE_RATE * dur)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    # Scale: D minor (D, F, G, A, C)
    bass_freqs = [73.42, 73.42, 87.31, 98.0] # D2, D2, F2, G2

    for b in range(total_beats):
        b_start = b * beat_dur
        s_idx = int(SAMPLE_RATE * b_start)

        # 1. Bass Pulse on every beat
        t_b = np.linspace(0, 0.42, int(SAMPLE_RATE * 0.42), endpoint=False)
        bfreq = bass_freqs[(b // 4) % len(bass_freqs)]
        b_env = np.exp(-t_b * 6.5)
        bass = (np.sin(2 * np.pi * bfreq * t_b) * 0.55 + np.sin(2 * np.pi * (bfreq * 2) * t_b) * 0.25) * b_env

        e_idx = min(n_samples, s_idx + len(bass))
        left[s_idx:e_idx] += bass[:e_idx-s_idx] * 0.6
        right[s_idx:e_idx] += bass[:e_idx-s_idx] * 0.6

        # 2. Tech hi-hat click on every 8th note
        for sub in [0.0, 0.25]:
            sub_idx = int(SAMPLE_RATE * (b_start + sub))
            t_hh = np.linspace(0, 0.05, int(SAMPLE_RATE * 0.05), endpoint=False)
            hh = np.random.normal(0, 0.2, len(t_hh)) * np.exp(-t_hh * 90)
            hh_end = min(n_samples, sub_idx + len(hh))
            left[sub_idx:hh_end] += hh[:hh_end-sub_idx] * 0.25
            right[sub_idx:hh_end] += hh[:hh_end-sub_idx] * 0.35

        # 3. Synth Arp Melody
        arp_notes = [293.66, 349.23, 392.0, 440.0, 523.25]
        m_freq = arp_notes[(b * 3) % len(arp_notes)]
        t_m = np.linspace(0, 0.22, int(SAMPLE_RATE * 0.22), endpoint=False)
        m_env = np.exp(-t_m * 12.0)
        lead = (np.sin(2 * np.pi * m_freq * t_m) * 0.22 + np.sin(2 * np.pi * (m_freq * 2) * t_m) * 0.08) * m_env
        m_end = min(n_samples, s_idx + len(lead))
        left[s_idx:m_end] += lead[:m_end-s_idx] * 0.4
        right[s_idx:m_end] += lead[:m_end-s_idx] * 0.5

    save_stereo_wav(filepath, left, right)


def make_bgm_lofi_chill(filepath: Path):
    """
    Lo-Fi Chill & Podcast Beat (32s loopable, 80 BPM).
    Soft Rhodes electric piano chords + gentle vinyl warmth.
    """
    bpm = 80
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4 # 3.0s
    total_bars = 10
    dur = bar_dur * total_bars
    n_samples = int(SAMPLE_RATE * dur)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    # Chords: Cmaj7, Am7, Dm7, G7 (warm jazz progression)
    chords = [
        [130.81, 164.81, 196.0, 246.94], # Cmaj7
        [110.0, 130.81, 164.81, 196.0],  # Am7
        [146.83, 174.61, 220.0, 261.63], # Dm7
        [98.0, 123.47, 146.83, 174.61],  # G7
    ]

    for bar in range(total_bars):
        c_notes = chords[bar % len(chords)]
        b_start = bar * bar_dur
        s_idx = int(SAMPLE_RATE * b_start)

        # Rhodes E-Piano warm chords on beats 1 and 3
        for beat in [0.0, 2.0]:
            p_start = b_start + beat * beat_dur
            p_idx = int(SAMPLE_RATE * p_start)
            t_c = np.linspace(0, 2.2, int(SAMPLE_RATE * 2.2), endpoint=False)
            c_env = np.exp(-t_c * 2.2)
            chord_snd = np.zeros(len(t_c))
            for f in c_notes:
                chord_snd += (np.sin(2 * np.pi * f * t_c) * 0.18 + np.sin(2 * np.pi * (f * 2) * t_c) * 0.06)
            chord_snd *= c_env
            c_end = min(n_samples, p_idx + len(chord_snd))
            left[p_idx:c_end] += chord_snd[:c_end-p_idx] * 0.55
            right[p_idx:c_end] += chord_snd[:c_end-p_idx] * 0.60

        # Gentle Lo-Fi Kick on beat 1 & Snare rim click on beat 3
        for bt in range(4):
            t_beat = b_start + bt * beat_dur
            b_sample = int(SAMPLE_RATE * t_beat)
            if bt in (0, 2):
                # Kick
                t_k = np.linspace(0, 0.25, int(SAMPLE_RATE * 0.25), endpoint=False)
                kick = np.sin(2 * np.pi * (90 * np.exp(-t_k * 25) + 40) * t_k) * np.exp(-t_k * 14) * 0.4
                k_end = min(n_samples, b_sample + len(kick))
                left[b_sample:k_end] += kick[:k_end-b_sample]
                right[b_sample:k_end] += kick[:k_end-b_sample]
            elif bt in (1, 3):
                # Soft Snare
                t_sn = np.linspace(0, 0.15, int(SAMPLE_RATE * 0.15), endpoint=False)
                sn = np.random.normal(0, 0.25, len(t_sn)) * np.exp(-t_sn * 28)
                sn_end = min(n_samples, b_sample + len(sn))
                left[b_sample:sn_end] += sn[:sn_end-b_sample] * 0.35
                right[b_sample:sn_end] += sn[:sn_end-b_sample] * 0.35

    save_stereo_wav(filepath, left, right)


def make_bgm_dramatic(filepath: Path):
    """
    Dramatic & Suspense Thriller Beat (30s loopable, 85 BPM).
    Pulsing dark bass + tension swell.
    """
    dur = 30.0
    n_samples = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n_samples, endpoint=False)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    # 1. Dark Bass Pulse (every 0.705s = 85 BPM)
    pulse_period = 60.0 / 85.0
    n_pulses = int(dur / pulse_period)
    for p in range(n_pulses):
        s_idx = int(SAMPLE_RATE * p * pulse_period)
        t_p = np.linspace(0, 0.55, int(SAMPLE_RATE * 0.55), endpoint=False)
        p_env = np.exp(-t_p * 7.0)
        # Deep minor bass
        bass = (np.sin(2 * np.pi * 55.0 * t_p) * 0.65 + np.sin(2 * np.pi * 110.0 * t_p) * 0.25) * p_env
        p_end = min(n_samples, s_idx + len(bass))
        left[s_idx:p_end] += bass[:p_end-s_idx] * 0.7
        right[s_idx:p_end] += bass[:p_end-s_idx] * 0.7

    # 2. Tension Swell strings
    swell_env = (np.sin(2 * np.pi * (t / 7.5)) ** 2) * 0.25
    strings = (
        np.sin(2 * np.pi * 220.0 * t) * 0.3 +
        np.sin(2 * np.pi * 261.6 * t) * 0.25 +
        np.sin(2 * np.pi * 329.6 * t) * 0.2
    ) * swell_env
    left += strings * 0.6
    right += strings * 0.75

    save_stereo_wav(filepath, left, right)


def make_bgm_happy_vlog(filepath: Path):
    """
    Happy & Upbeat Vlog Acoustic Music (30s loopable, 115 BPM).
    Bright acoustic guitar strum + bell melody.
    """
    bpm = 115
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    total_bars = 14
    dur = bar_dur * total_bars
    n_samples = int(SAMPLE_RATE * dur)
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)

    # Major progression: C - G - Am - F
    major_chords = [
        [261.63, 329.63, 392.0, 523.25], # C
        [196.0, 246.94, 293.66, 392.0],  # G
        [220.0, 261.63, 329.63, 440.0],  # Am
        [174.61, 220.0, 261.63, 349.23], # F
    ]

    for bar in range(total_bars):
        c_notes = major_chords[bar % len(major_chords)]
        b_start = bar * bar_dur

        # Acoustic Guitar Strum on 8th notes
        for eighth in range(8):
            st_time = b_start + eighth * (beat_dur / 2.0)
            st_idx = int(SAMPLE_RATE * st_time)
            t_s = np.linspace(0, 0.35, int(SAMPLE_RATE * 0.35), endpoint=False)
            s_env = np.exp(-t_s * 15.0)
            strum = np.zeros(len(t_s))
            for f in c_notes:
                strum += np.sin(2 * np.pi * f * t_s) * 0.12
            strum *= s_env
            st_end = min(n_samples, st_idx + len(strum))
            left[st_idx:st_end] += strum[:st_end-st_idx] * 0.5
            right[st_idx:st_end] += strum[:st_end-st_idx] * 0.55

        # Cheerful Bell melody every 2 beats
        for m_beat in [0, 2]:
            m_time = b_start + m_beat * beat_dur
            m_idx = int(SAMPLE_RATE * m_time)
            m_freq = c_notes[1] * 2.0
            t_m = np.linspace(0, 0.6, int(SAMPLE_RATE * 0.6), endpoint=False)
            m_env = np.exp(-t_m * 6.0)
            bell = (np.sin(2 * np.pi * m_freq * t_m) * 0.22 + np.sin(2 * np.pi * (m_freq * 2) * t_m) * 0.08) * m_env
            m_end = min(n_samples, m_idx + len(bell))
            left[m_idx:m_end] += bell[:m_end-m_idx] * 0.6
            right[m_idx:m_end] += bell[:m_end-m_idx] * 0.4

    save_stereo_wav(filepath, left, right)


def main():
    print("\n" + "=" * 65)
    print("    AUTOCAPCUT STUDIO - TẠO KHO ÂM THANH SFX VÀ BGM CHUẨN CAPCUT")
    print("=" * 65 + "\n")

    # 1. Generate SFX Collection
    print("1. Đang tạo các hiệu ứng âm thanh chuyển cảnh (SFX)...")
    sfx_list = [
        ("whoosh_cinematic_deep.wav", make_whoosh_cinematic_deep),
        ("whoosh_fast.wav", make_whoosh_fast),
        ("whoosh_soft_air.wav", make_whoosh_soft_air),
        ("whoosh_heavy_bass.wav", make_whoosh_heavy_bass),
        ("swoosh_fast_whip.wav", make_swoosh_fast_whip),
        ("swoosh_slide.wav", make_swoosh_slide),
        ("camera_shutter.wav", make_camera_shutter),
        ("mouse_click.wav", make_mouse_click),
        ("keyboard_typing.wav", make_keyboard_typing),
        ("bubble_pop.wav", make_bubble_pop),
        ("cash_register_kaching.wav", make_cash_register_kaching),
        ("cinematic_boom_impact.wav", make_cinematic_boom_impact),
        ("bell_ding_chime.wav", make_bell_ding_chime),
        ("tape_rewind.wav", make_tape_rewind),
        ("glitch_digital.wav", make_glitch_digital),
    ]

    for fname, func in sfx_list:
        path = SFX_DIR / fname
        func(path)
        print(f"   [+] SFX: {fname}")

    # 2. Generate BGM Presets
    print("\n2. Đang tạo kho nhạc nền có sẵn chuẩn CapCut (BGM)...")
    bgm_list = [
        ("cinematic_storytelling.wav", make_bgm_cinematic, "Điện ảnh & Cảm xúc (Cinematic Piano/Strings)"),
        ("news_finance_tech.wav", make_bgm_news_tech, "Tin tức & Tài chính (Modern Tech News)"),
        ("lofi_chill_podcast.wav", make_bgm_lofi_chill, "Thư giãn & Lofi Chill (Lofi Beats)"),
        ("dramatic_suspense.wav", make_bgm_dramatic, "Kịch tính & Hồi hộp (Suspense Thriller)"),
        ("happy_vlog_upbeat.wav", make_bgm_happy_vlog, "Vui tươi & Năng động (Happy Vlog)"),
    ]

    for fname, func, desc in bgm_list:
        path = BGM_DIR / fname
        func(path)
        print(f"   [+] BGM: {fname} ({desc})")

    print("\n" + "=" * 65)
    print("🎉 TẠO KHO ÂM THANH SFX & BGM HOÀN TẤT THÀNH CÔNG!")
    print(f"   Thư mục SFX: {SFX_DIR}")
    print(f"   Thư mục BGM: {BGM_DIR}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
