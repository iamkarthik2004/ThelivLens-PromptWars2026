from pathlib import Path
from uuid import uuid4
import re

class LocalObjectStorage:
    def __init__(self, directory: str = "uploads"): self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
    async def put(self, filename: str, data: bytes, content_type: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)[:120]
        key = f"uploads/{uuid4()}-{safe}"; path = Path(key); path.parent.mkdir(exist_ok=True); path.write_bytes(data); return str(path)
