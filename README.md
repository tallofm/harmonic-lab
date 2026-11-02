# harmonic-lab

A lightweight acoustic physics and harmonic progression synthesizer web application. Combines music theory, wave mechanics, and browser-based Web Audio API playback with a serverless Python backend for binary MIDI generation.

## Features
- **Acoustic Wave Physics**: Computes the natural harmonic overtone series ($f_n = n \cdot f_1$) and relative power amplitudes ($1/n$).
- **Psychoacoustic Consonance**: Estimates interval dissonance using the Plomp-Levelt critical bandwidth roughness model.
- **Zero-Dependency MIDI Generation**: Pure Python `struct` encoder that outputs standard Type-0 `.mid` files.
- **Web Audio Synth**: Real-time sine-wave synthesizer in vanilla JavaScript.
- **Serverless API**: Python function running on Vercel (`api/index.py`).

## Project Structure
```
harmonic-lab/
├── api/
│   └── index.py            # Vercel serverless request handler (GET & POST)
├── harmonic_engine.py      # Core acoustics, notes, intervals, and MIDI encoder
├── public/
│   └── index.html          # Interactive workstation interface & Web Audio player
├── tests/
│   └── test_harmonic_engine.py # Unit test suite
└── vercel.json             # Deployment routing configuration
```

## Setup & Testing

### Run Tests
```bash
python3 -m unittest tests/test_harmonic_engine.py
```

### Run Frontend Locally
```bash
python3 -m http.server 3000 --directory public
```
Open `http://localhost:3000` in your browser.

## API Contracts

### `GET /api`
Calculates note frequencies, consonance score, and overtone harmonics.
- **Query Params**:
  - `root` (string, default: `C4`): Root note name and octave.
  - `type` (string, default: `maj7`): Chord quality (`major`, `minor`, `maj7`, `min7`, `dom7`, `dim`, `aug`, `sus4`, `add9`).
  - `harmonics` (int, default: `8`): Number of harmonic overtones to generate.

### `POST /api`
Generates and downloads a binary `.mid` chord progression file.
- **Payload**:
  ```json
  {
    "progression": [["C4", "maj7"], ["A3", "min7"], ["D4", "min7"], ["G3", "dom7"]],
    "bpm": 120
  }
  ```

## Known Limitations & Roadmap
- [ ] Slash chords / chord inversions (e.g. `C/E`) are currently not parsed.
- [ ] Direct single-chord MIDI download via `GET /api/midi` returns JSON instead of binary stream.
- [ ] Microtonal alternate temperaments (Just Intonation, Mean-tone) are not yet implemented.
- [ ] Query parameter validation is missing upper bounds on `harmonics`.
