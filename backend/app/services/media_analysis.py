from pathlib import Path
from PIL import Image

async def extract_metadata(path: str | Path, media_type: str) -> dict:
    p = Path(path)
    result = {"format": p.suffix.lstrip(".").upper(), "size_bytes": p.stat().st_size}
    if media_type == "image":
        try:
            with Image.open(p) as im:
                result.update({"width": im.width, "height": im.height, "format": im.format, "exif": dict(im.getexif()) if im.getexif() else {}})
        except Exception:
            result["note"] = "Image metadata could not be parsed."
    else:
        result["note"] = "Detailed media metadata requires ffprobe/librosa and was not available."
    return result
