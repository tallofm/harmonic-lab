"""
Vercel Serverless API Handler
-----------------------------
Routes:
- GET  /api: Acoustic calculations, consonance scoring, and overtone analysis
- POST /api: Generates and streams Standard MIDI Files (.mid) from chord progressions
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import sys
import os

# Ensure parent directory is on sys.path to import harmonic_engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harmonic_engine


class handler(BaseHTTPRequestHandler):

    def _send_problem(self, status: int, title: str, detail: str, error_type: str = "bad-request"):
        """Emit an RFC 7807 compliant application/problem+json response."""
        problem = {
            "type": f"https://harmoniclab.vercel.app/errors/{error_type}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": self.path
        }
        body = json.dumps(problem, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/problem+json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict, status: int = 200):
        """Emit a standard JSON response with CORS headers."""
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)

        # Route: /api/harmonics or /api
        # TODO: Route GET /api/midi requests directly to binary stream instead of JSON response
        # TODO: Add boundary validation for harmonics (currently unbounded, could cause compute timeouts)
        root_note = params.get("root", ["C4"])[0]
        chord_type = params.get("type", ["maj7"])[0]
        harmonics_count = int(params.get("harmonics", ["8"])[0])

        try:
            midi_notes = harmonic_engine.get_chord_notes(root_note, chord_type)
            root_freq = harmonic_engine.note_to_frequency(root_note)
            frequencies = [round(harmonic_engine.midi_to_frequency(m), 2) for m in midi_notes]
            overtones = harmonic_engine.calculate_overtones(root_freq, num_harmonics=harmonics_count)
            consonance = harmonic_engine.estimate_consonance_score(frequencies)

            response_data = {
                "root_note": root_note,
                "chord_type": chord_type,
                "midi_notes": midi_notes,
                "frequencies_hz": frequencies,
                "consonance_score": consonance,
                "overtone_series": overtones,
                "links": {
                    "self": self.path,
                    "midi_download": f"/api/midi?root={root_note}&type={chord_type}"
                }
            }
            self._send_json(response_data)

        except ValueError as err:
            self._send_problem(
                status=400,
                title="Invalid Parameter",
                detail=str(err),
                error_type="invalid-parameter"
            )
        except Exception as err:
            self._send_problem(
                status=500,
                title="Internal Engine Error",
                detail=str(err),
                error_type="engine-fault"
            )

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
            progression = payload.get("progression", [["C4", "maj7"], ["A3", "min7"], ["D4", "min7"], ["G3", "dom7"]])
            bpm = int(payload.get("bpm", 120))

            midi_chords = []
            for root, ctype in progression:
                midi_chords.append(harmonic_engine.get_chord_notes(root, ctype))

            midi_bytes = harmonic_engine.generate_midi_bytes(midi_chords, bpm=bpm)

            self.send_response(200)
            self.send_header("Content-Type", "audio/midi")
            self.send_header("Content-Disposition", 'attachment; filename="progression.mid"')
            self.send_header("Content-Length", str(len(midi_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(midi_bytes)

        except Exception as err:
            self._send_problem(
                status=400,
                title="MIDI Generation Failed",
                detail=str(err),
                error_type="midi-generation-failed"
            )
