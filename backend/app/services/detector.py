"""Forensic signal interface. Replace this fallback with a trained detector later."""
import hashlib
from pathlib import Path

def detect_media(file_path: str | Path, media_type: str, metadata: dict | None = None) -> dict:
    path = Path(file_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    # This is deliberately a deterministic, non-trained baseline; it is not a deepfake detector.
    score = int(digest[:4], 16) % 23 + 78
    return {"ai_probability": score, "manipulation_probability": max(0, score - 25),
            "authentic_probability": max(0, 100 - score),
            "signals": [{"name": "File-level forensic baseline", "description": "Heuristic checksum/metadata baseline; no trained classifier is installed.", "confidence": 35}],
            "is_fallback": True}
