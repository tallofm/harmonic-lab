"""
Unit tests for the Harmonic Lab acoustic engine and MIDI generator.
Covers frequency conversion, chord intervals, overtone series, and binary MIDI encoding.
"""

import unittest
from harmonic_engine import (
    note_to_midi,
    midi_to_frequency,
    note_to_frequency,
    get_chord_notes,
    calculate_overtones,
    estimate_consonance_score,
    generate_midi_bytes
)

class TestHarmonicEngine(unittest.TestCase):

    def test_note_to_midi_a4(self):
        # A4 is standard MIDI note 69
        self.assertEqual(note_to_midi("A4"), 69)
        self.assertEqual(note_to_midi("C4"), 60)
        self.assertEqual(note_to_midi("C#4"), 61)
        self.assertEqual(note_to_midi("Db4"), 61)

    def test_midi_to_frequency_a440(self):
        # A4 (69) is exactly 440.0 Hz
        freq = midi_to_frequency(69)
        self.assertAlmostEqual(freq, 440.0, places=2)

        # C4 (60) is approx 261.63 Hz
        c4_freq = midi_to_frequency(60)
        self.assertAlmostEqual(c4_freq, 261.63, places=2)

    def test_note_to_frequency(self):
        self.assertAlmostEqual(note_to_frequency("A4"), 440.0, places=2)

    def test_get_chord_notes_major(self):
        # C Major: C4, E4, G4 (MIDI 60, 64, 67)
        chord = get_chord_notes("C4", "major")
        self.assertEqual(chord, [60, 64, 67])

    def test_get_chord_notes_maj7(self):
        # Cmaj7: C4, E4, G4, B4 (MIDI 60, 64, 67, 71)
        chord = get_chord_notes("C4", "maj7")
        self.assertEqual(chord, [60, 64, 67, 71])

    def test_get_chord_notes_min7(self):
        # Am7: A3, C4, E4, G4 (MIDI 57, 60, 64, 67)
        chord = get_chord_notes("A3", "min7")
        self.assertEqual(chord, [57, 60, 64, 67])

    def test_calculate_overtones(self):
        # Fundamental: 100 Hz
        overtones = calculate_overtones(100.0, num_harmonics=4)
        self.assertEqual(len(overtones), 4)
        self.assertEqual(overtones[0]["harmonic"], 1)
        self.assertAlmostEqual(overtones[0]["frequency"], 100.0)
        self.assertEqual(overtones[1]["harmonic"], 2)
        self.assertAlmostEqual(overtones[1]["frequency"], 200.0)
        self.assertEqual(overtones[2]["harmonic"], 3)
        self.assertAlmostEqual(overtones[2]["frequency"], 300.0)

    def test_consonance_octave_vs_tritone(self):
        # Perfect octave (60 and 72) should have a higher consonance score than a minor second (60 and 61)
        octave_score = estimate_consonance_score([261.63, 523.25])
        minor_second_score = estimate_consonance_score([261.63, 277.18])
        self.assertGreater(octave_score, minor_second_score)

    def test_generate_midi_bytes_valid_header(self):
        # MIDI file must begin with header chunk "MThd"
        progression = [[60, 64, 67], [57, 60, 64]]
        midi_data = generate_midi_bytes(progression, bpm=120)
        self.assertTrue(isinstance(midi_data, bytes))
        self.assertTrue(midi_data.startswith(b"MThd"))
        # Track chunk starts with "MTrk"
        self.assertIn(b"MTrk", midi_data)

if __name__ == "__main__":
    unittest.main()
