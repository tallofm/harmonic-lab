"""
Harmonic Lab Core Engine
------------------------
Pure Python acoustic physics, music theory calculations, and Standard MIDI generation.
Zero external dependencies for deployment on Vercel Serverless Functions.
"""

import math
import struct
from typing import List, Dict, Any

NOTE_NAMES = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
}

# Supported chord intervals (semitones above root)
# TODO: Add sus2, 9th, 11th, and half-diminished voicings
# TODO: Add slash chord inversion parser (e.g. 'C4/E' -> shift root to bass)
CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14],
}

HARMONIC_NAMES = [
    "Fundamental (1st)", "Octave (2nd)", "Fifth (3rd)", "Double Octave (4th)",
    "Major Third (5th)", "Fifth (6th)", "Harmonic 7th (7th)", "Triple Octave (8th)",
    "Major Second (9th)", "Major Third (10th)", "Tritone/11th (11th)", "Fifth (12th)"
]


def note_to_midi(note_str: str) -> int:
    """
    Parse a note string like 'C4', 'A#3', 'Eb5' into a standard MIDI note number (0-127).
    Middle C (C4) = 60.
    """
    note_str = note_str.strip().upper()
    if len(note_str) < 2:
        raise ValueError(f"Invalid note format: '{note_str}'")

    if note_str[1] in ("#", "B"):
        pitch_name = note_str[:2]
        octave_str = note_str[2:]
    else:
        pitch_name = note_str[:1]
        octave_str = note_str[1:]

    if pitch_name not in NOTE_NAMES:
        raise ValueError(f"Unknown note name: '{pitch_name}'")

    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"Invalid octave in note: '{note_str}'")

    semitone = NOTE_NAMES[pitch_name]
    # Standard formula: (octave + 1) * 12 + semitone. C4 = (4+1)*12 + 0 = 60.
    midi_note = (octave + 1) * 12 + semitone
    if not (0 <= midi_note <= 127):
        raise ValueError(f"Note out of MIDI range [0-127]: '{note_str}' -> {midi_note}")

    return midi_note


def midi_to_frequency(midi_note: int, concert_pitch_a4: float = 440.0) -> float:
    """
    Calculate equal temperament frequency from MIDI note number.
    Formula: f = A4 * 2^((midi - 69) / 12)
    """
    return concert_pitch_a4 * (2.0 ** ((midi_note - 69) / 12.0))


def note_to_frequency(note_str: str, concert_pitch_a4: float = 440.0) -> float:
    """Directly calculate frequency for a note string (e.g., 'A4' -> 440.0)."""
    return midi_to_frequency(note_to_midi(note_str), concert_pitch_a4)


def get_chord_notes(root_note: str, chord_type: str = "major") -> List[int]:
    """Return MIDI note numbers for a chord given a root note and chord type."""
    root_midi = note_to_midi(root_note)
    chord_key = chord_type.lower()
    if chord_key not in CHORD_INTERVALS:
        raise ValueError(f"Unsupported chord type '{chord_type}'. Supported: {list(CHORD_INTERVALS.keys())}")

    intervals = CHORD_INTERVALS[chord_key]
    return [root_midi + interval for interval in intervals]


def calculate_overtones(fundamental_freq: float, num_harmonics: int = 8) -> List[Dict[str, Any]]:
    """
    Compute harmonic overtone series fn = n * f1.
    Includes theoretical amplitude (1/n) and interval labels.
    """
    overtones = []
    for n in range(1, num_harmonics + 1):
        freq = fundamental_freq * n
        label = HARMONIC_NAMES[n - 1] if n - 1 < len(HARMONIC_NAMES) else f"{n}th Harmonic"
        overtones.append({
            "harmonic": n,
            "frequency": round(freq, 2),
            "relative_amplitude": round(1.0 / n, 4),
            "interval_label": label
        })
    return overtones


def estimate_consonance_score(frequencies: List[float]) -> float:
    """
    Compute a consonance score [0.0 - 100.0] for a collection of frequencies
    based on the Plomp-Levelt psychoacoustic dissonance model.
    """
    if len(frequencies) < 2:
        return 100.0

    total_roughness = 0.0
    pairs = 0

    for i in range(len(frequencies)):
        for j in range(i + 1, len(frequencies)):
            f1 = min(frequencies[i], frequencies[j])
            f2 = max(frequencies[i], frequencies[j])
            df = f2 - f1
            if f1 <= 0 or df <= 0:
                continue

            # Critical bandwidth around f1
            cbw = 1.72 * (f1 ** 0.65)
            x = df / cbw

            # Plomp-Levelt roughness curve: r(x) = e * (x/x_max) * exp(-x/x_max)
            # peaks near x = 0.24 (maximum dissonance occurs at ~1/4 critical bandwidth)
            roughness = (math.e / 0.24) * x * math.exp(-x / 0.24)
            total_roughness += roughness
            pairs += 1

    avg_roughness = total_roughness / max(pairs, 1)
    # Convert roughness into a 0 - 100 consonance score
    consonance = max(0.0, min(100.0, 100.0 - (avg_roughness * 35.0)))
    return round(consonance, 1)


def _encode_variable_length(val: int) -> bytes:
    """Encode an integer as a MIDI variable-length quantity."""
    buf = bytearray()
    buf.append(val & 0x7F)
    val >>= 7
    while val > 0:
        buf.append((val & 0x7F) | 0x80)
        val >>= 7
    buf.reverse()
    return bytes(buf)


def generate_midi_bytes(chord_progression: List[List[int]], bpm: int = 120) -> bytes:
    """
    Generate a valid Standard MIDI File (Type 0, single track) from chord progression.
    Pure Python standard library (struct) — zero external packages required.
    """
    ticks_per_beat = 480
    ticks_per_chord = ticks_per_beat * 4  # 4 beats (1 full 4/4 measure per chord)
    microseconds_per_beat = int(60_000_000 / bpm)

    track_events = bytearray()

    # Meta event: Set Tempo (Delta time = 0)
    tempo_bytes = microseconds_per_beat.to_bytes(3, 'big')
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x51\x03" + tempo_bytes)

    # Meta event: Track Name
    name_bytes = b"HarmonicLab Chord Track"
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x03" + bytes([len(name_bytes)]) + name_bytes)

    # Program change: Electric Piano (instrument 4)
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xC0\x04")

    # Add chords
    for chord in chord_progression:
        # Note On for all notes in chord (delta = 0)
        for note in chord:
            track_events.extend(_encode_variable_length(0))
            track_events.extend(bytes([0x90, note & 0x7F, 85])) # Note On, velocity 85

        # Note Off after 1 bar
        for idx, note in enumerate(chord):
            # First note carries the duration delay, subsequent notes delta = 0
            dt = ticks_per_chord if idx == 0 else 0
            track_events.extend(_encode_variable_length(dt))
            track_events.extend(bytes([0x80, note & 0x7F, 64])) # Note Off

    # End of Track meta event (delta = 0)
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x2F\x00")

    # Build MThd header chunk:
    # 4 bytes 'MThd', 4 bytes length (6), 2 bytes format (0), 2 bytes tracks (1), 2 bytes division (ticks_per_beat)
    header_chunk = struct.pack(">4sIHHH", b"MThd", 6, 0, 1, ticks_per_beat)

    # Build MTrk track chunk:
    # 4 bytes 'MTrk', 4 bytes length, followed by track events
    track_chunk = struct.pack(">4sI", b"MTrk", len(track_events)) + bytes(track_events)

    return header_chunk + track_chunk
