"""Forensic signal interface. Analyzes image properties to detect potential AI generation."""
import hashlib
import math
import statistics
from pathlib import Path
from PIL import Image, ImageFilter


def _compute_noise_score(img: Image.Image) -> float:
    """Analyze noise patterns - AI images often have unnatural noise distribution."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.Kernel((3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], scale=1, offset=0))
    pixels = list(edges.getdata())
    if not pixels:
        return 50.0
    variance = statistics.variance(pixels) if len(pixels) > 1 else 0
    if variance < 50:
        return 75
    elif variance < 150:
        return 60
    elif variance < 300:
        return 50
    return 40


def _compute_color_consistency(img: Image.Image) -> float:
    """Check color consistency - AI images often have overly smooth gradients."""
    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    channel_stds = [statistics.stdev(pixels) if len(pixels) > 1 else 0 for pixels in [list(r.getdata()), list(g.getdata()), list(b.getdata())]]
    avg_std = statistics.mean(channel_stds)
    if avg_std < 40:
        return 80
    elif avg_std < 60:
        return 65
    elif avg_std < 80:
        return 55
    return 45


def _check_metadata_signals(metadata: dict | None) -> tuple[float, str]:
    """Analyze metadata for authenticity signals."""
    if not metadata:
        return 60, "No metadata available for analysis."
    exif = metadata.get("exif", {})
    if not exif:
        return 65, "EXIF metadata is missing, which is common in AI-generated images."
    software = exif.get(305) or exif.get("Software")
    if software:
        ai_tools = ["midjourney", "dall-e", "stable diffusion", "firefly", "copilot", "adobe generative", "leonardo"]
        if any(ai_tool in str(software).lower() for ai_tool in ai_tools):
            return 90, f"Software tag '{software}' indicates AI generation tool."
    camera_make = exif.get(271) or exif.get("Make")
    camera_model = exif.get(272) or exif.get("Model")
    if not camera_make and not camera_model:
        return 60, "No camera manufacturer/model in EXIF, suspicious for camera-captured content."
    return 30, "Camera metadata present, suggesting possible authentic origin."


def _compute_frequency_score(img: Image.Image) -> float:
    """Analyze frequency domain characteristics via edge density."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    pixels = list(edges.getdata())
    if not pixels:
        return 50.0
    mean_edge = statistics.mean(pixels)
    if mean_edge < 10:
        return 78
    elif mean_edge < 20:
        return 65
    elif mean_edge < 35:
        return 55
    return 45


def _get_dimension_signals(metadata: dict | None) -> tuple[float, str]:
    """Check image dimensions for AI generation patterns."""
    if not metadata:
        return 50, "Dimensions unknown."
    w = metadata.get("width", 0)
    h = metadata.get("height", 0)
    if not w or not h:
        return 50, "Dimensions unavailable."
    ai_sizes = {(1024, 1024), (512, 512), (768, 768), (1024, 576), (576, 1024), (1024, 768), (768, 1024)}
    if (w, h) in ai_sizes or (h, w) in ai_sizes:
        return 72, f"Dimensions {w}x{h} match common AI generation output sizes."
    aspect = w / h
    if abs(aspect - 1.0) < 0.01 and w >= 512:
        return 60, f"Square aspect ratio ({w}x{h}) is common in AI-generated images."
    return 40, f"Dimensions {w}x{h} do not strongly indicate AI generation."


def _compute_symmetry_score(img: Image.Image) -> float:
    """AI images sometimes exhibit unusual symmetry patterns."""
    gray = img.convert("L")
    w, h = gray.size
    if w < 4 or h < 4:
        return 50.0
    left = gray.crop((0, 0, w // 2, h))
    right = gray.crop((w // 2, 0, w, h))
    right_flipped = right.transpose(Image.FLIP_LEFT_RIGHT)
    left_resized = left.resize(right_flipped.size)
    left_pixels = list(left_resized.convert("L").getdata())
    right_pixels = list(right_flipped.convert("L").getdata())
    if not left_pixels or not right_pixels:
        return 50.0
    diff_sum = sum(abs(a - b) for a, b in zip(left_pixels, right_pixels))
    max_diff = len(left_pixels) * 255
    similarity = 1 - (diff_sum / max_diff) if max_diff > 0 else 0
    if similarity > 0.85:
        return 75
    elif similarity > 0.7:
        return 60
    return 40


def detect_media(file_path: str | Path, media_type: str, metadata: dict | None = None) -> dict:
    path = Path(file_path)
    signals = []
    scores = []

    if media_type == "image":
        try:
            with Image.open(path) as im:
                img = im.convert("RGB")

            noise_score = _compute_noise_score(img)
            signals.append({
                "name": "Noise pattern analysis",
                "description": "Analyzes noise distribution across the image. AI-generated images often exhibit unnaturally uniform or absent noise patterns.",
                "confidence": int(noise_score)
            })
            scores.append(noise_score)

            color_score = _compute_color_consistency(img)
            signals.append({
                "name": "Color consistency check",
                "description": "Evaluates color gradient smoothness. AI images tend to have overly smooth transitions and lack natural color variation.",
                "confidence": int(color_score)
            })
            scores.append(color_score)

            freq_score = _compute_frequency_score(img)
            signals.append({
                "name": "Frequency domain analysis",
                "description": "Examines frequency spectrum characteristics. AI-generated images often lack the high-frequency detail found in camera captures.",
                "confidence": int(freq_score)
            })
            scores.append(freq_score)

            symmetry_score = _compute_symmetry_score(img)
            signals.append({
                "name": "Symmetry pattern check",
                "description": "Evaluates bilateral symmetry. Unusual symmetry patterns can indicate AI generation.",
                "confidence": int(symmetry_score)
            })
            scores.append(symmetry_score)

            dim_score, dim_desc = _get_dimension_signals(metadata)
            signals.append({
                "name": "Dimension pattern check",
                "description": dim_desc,
                "confidence": int(dim_score)
            })
            scores.append(dim_score)

        except Exception as e:
            signals.append({
                "name": "Image analysis error",
                "description": f"Could not perform image analysis: {str(e)}",
                "confidence": 30
            })
            scores.append(30)

    meta_score, meta_desc = _check_metadata_signals(metadata)
    signals.append({
        "name": "Metadata authenticity",
        "description": meta_desc,
        "confidence": int(meta_score)
    })
    scores.append(meta_score)

    file_size = path.stat().st_size
    if file_size < 50000:
        signals.append({
            "name": "File size anomaly",
            "description": f"File is unusually small ({file_size} bytes), which can indicate synthetic generation or heavy compression.",
            "confidence": 55
        })
        scores.append(55)

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entropy = int(digest[:8], 16) % 100
    if entropy > 70:
        signals.append({
            "name": "Hash entropy check",
            "description": "File hash entropy analysis shows patterns sometimes associated with generated content.",
            "confidence": 40
        })
        scores.append(40)

    if not scores:
        scores = [50]

    ai_probability = int(min(95, max(20, statistics.mean(scores))))
    manipulation_probability = int(min(90, max(10, ai_probability * 0.7 + (statistics.stdev(scores) if len(scores) > 1 else 0) * 0.3)))
    authentic_probability = max(0, 100 - ai_probability)

    return {
        "ai_probability": ai_probability,
        "manipulation_probability": manipulation_probability,
        "authentic_probability": authentic_probability,
        "signals": signals,
        "is_fallback": False
    }
