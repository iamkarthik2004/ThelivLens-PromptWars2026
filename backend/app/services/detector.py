"""Forensic signal interface. Analyzes image properties as a baseline signal.
NOTE: This is a lightweight heuristic detector - not a trained deepfake classifier.
The HuggingFace vision model provides the primary assessment when available."""
import hashlib
import statistics
from pathlib import Path
from PIL import Image, ImageFilter


def _compute_noise_score(img: Image.Image) -> tuple[float, str]:
    """Analyze edge strength - real photos have natural edge variation."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.Kernel((3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], scale=1, offset=0))
    pixels = list(edges.getdata())
    if not pixels:
        return 50.0, "Unable to compute noise analysis."
    variance = statistics.variance(pixels) if len(pixels) > 1 else 0
    # Real photos typically have moderate edge variance (100-800)
    # AI images can be either very smooth (low) or have artifacts (high)
    if variance < 30:
        return 65, "Very low edge variance detected. AI-generated images often have unnaturally smooth transitions."
    elif variance > 1000:
        return 60, "High edge variance detected. May indicate compression artifacts or generation artifacts."
    return 35, "Edge variance within normal range for camera-captured content."


def _compute_color_consistency(img: Image.Image) -> tuple[float, str]:
    """Check color consistency - real photos have natural color variation."""
    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    channel_stds = []
    for pixels in [list(r.getdata()), list(g.getdata()), list(b.getdata())]:
        if len(pixels) > 1:
            channel_stds.append(statistics.stdev(pixels))
    avg_std = statistics.mean(channel_stds) if channel_stds else 0
    # Real photos typically have std > 50
    if avg_std < 25:
        return 70, "Extremely low color variation. This is unusual for camera-captured content."
    elif avg_std < 40:
        return 55, "Low color variation detected. Could indicate AI generation or heavy processing."
    return 30, "Color variation is consistent with natural photography."


def _check_metadata_signals(metadata: dict | None) -> tuple[float, str]:
    """Analyze metadata for authenticity signals."""
    if not metadata:
        return 55, "No metadata available for analysis. This can happen with AI images or stripped EXIF."
    exif = metadata.get("exif", {})
    if not exif:
        return 50, "EXIF metadata is missing. This is common in AI-generated images and social media re-uploads."

    # Check for AI tool signatures in software tag
    software = exif.get(305) or exif.get("Software")
    if software:
        software_str = str(software).lower()
        ai_tools = ["midjourney", "dall-e", "stable diffusion", "firefly", "copilot", "adobe generative", "leonardo", "craiyon", "playground"]
        for ai_tool in ai_tools:
            if ai_tool in software_str:
                return 85, f"Software tag '{software}' indicates AI generation tool."

    # Check for camera make/model - strong authenticity signal
    camera_make = exif.get(271) or exif.get("Make")
    camera_model = exif.get(272) or exif.get("Model")
    if camera_make and camera_model:
        return 20, f"Camera metadata present ({camera_make} {camera_model}), suggesting authentic origin."
    elif camera_make:
        return 25, f"Camera manufacturer '{camera_make}' detected in metadata."
    elif camera_model:
        return 25, f"Camera model '{camera_model}' detected in metadata."

    # Has EXIF but no camera info
    has_datetime = exif.get(36867) or exif.get(306) or exif.get("DateTimeOriginal")
    if has_datetime:
        return 35, "EXIF timestamp present but no camera info. May be processed or edited."

    return 45, "Limited metadata available. Cannot strongly determine origin."


def _compute_frequency_score(img: Image.Image) -> tuple[float, str]:
    """Analyze edge density - real photos have natural frequency patterns."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    pixels = list(edges.getdata())
    if not pixels:
        return 50.0, "Unable to compute frequency analysis."
    mean_edge = statistics.mean(pixels)
    # Real photos typically have mean edge values between 15-40
    if mean_edge < 8:
        return 65, "Very low edge density. AI images sometimes lack natural high-frequency detail."
    elif mean_edge > 50:
        return 55, "Unusually high edge density. May indicate noise patterns from generation."
    return 30, "Frequency characteristics consistent with camera capture."


def _get_dimension_signals(metadata: dict | None) -> tuple[float, str]:
    """Check image dimensions for AI generation patterns."""
    if not metadata:
        return 45, "Dimensions unknown."
    w = metadata.get("width", 0)
    h = metadata.get("height", 0)
    if not w or not h:
        return 45, "Dimensions unavailable."
    # Common AI output sizes (not definitive - real cameras can produce these too)
    ai_sizes = {(1024, 1024), (512, 512), (768, 768)}
    if (w, h) in ai_sizes or (h, w) in ai_sizes:
        return 55, f"Dimensions {w}x{h} match common AI output sizes, but this is not definitive."
    return 35, f"Dimensions {w}x{h} are within normal range."


def _compute_symmetry_score(img: Image.Image) -> tuple[float, str]:
    """Check bilateral symmetry - extreme symmetry can indicate AI."""
    gray = img.convert("L")
    w, h = gray.size
    if w < 10 or h < 10:
        return 45.0, "Image too small for symmetry analysis."
    left = gray.crop((0, 0, w // 2, h))
    right = gray.crop((w // 2, 0, w, h))
    right_flipped = right.transpose(Image.FLIP_LEFT_RIGHT)
    left_resized = left.resize(right_flipped.size)
    left_pixels = list(left_resized.convert("L").getdata())
    right_pixels = list(right_flipped.convert("L").getdata())
    if not left_pixels or not right_pixels:
        return 45.0, "Unable to compute symmetry."
    diff_sum = sum(abs(a - b) for a, b in zip(left_pixels, right_pixels))
    max_diff = len(left_pixels) * 255
    similarity = 1 - (diff_sum / max_diff) if max_diff > 0 else 0
    # Perfect bilateral symmetry is rare in natural photos
    if similarity > 0.90:
        return 60, "Unusually high bilateral symmetry. This is uncommon in natural photographs."
    return 30, "Symmetry levels are within normal range."


def detect_media(file_path: str | Path, media_type: str, metadata: dict | None = None) -> dict:
    """Analyze media and return forensic signals.
    
    Returns ai_probability (0-100) where higher = more likely AI-generated.
    Real photos with camera metadata should score 20-40.
    AI-generated content should score 60-90.
    """
    path = Path(file_path)
    signals = []
    scores = []
    weights = []

    if media_type == "image":
        try:
            with Image.open(path) as im:
                img = im.convert("RGB")

            # Each signal contributes differently
            noise_score, noise_desc = _compute_noise_score(img)
            signals.append({"name": "Noise pattern analysis", "description": noise_desc, "confidence": int(noise_score)})
            scores.append(noise_score)
            weights.append(1.0)

            color_score, color_desc = _compute_color_consistency(img)
            signals.append({"name": "Color consistency check", "description": color_desc, "confidence": int(color_score)})
            scores.append(color_score)
            weights.append(1.0)

            freq_score, freq_desc = _compute_frequency_score(img)
            signals.append({"name": "Frequency domain analysis", "description": freq_desc, "confidence": int(freq_score)})
            scores.append(freq_score)
            weights.append(0.8)

            symmetry_score, sym_desc = _compute_symmetry_score(img)
            signals.append({"name": "Symmetry pattern check", "description": sym_desc, "confidence": int(symmetry_score)})
            scores.append(symmetry_score)
            weights.append(0.7)

            dim_score, dim_desc = _get_dimension_signals(metadata)
            signals.append({"name": "Dimension pattern check", "description": dim_desc, "confidence": int(dim_score)})
            scores.append(dim_score)
            weights.append(0.5)

        except Exception as e:
            signals.append({"name": "Image analysis error", "description": f"Could not analyze image: {str(e)}", "confidence": 30})
            scores.append(30)
            weights.append(0.5)

    # Metadata is a strong signal
    meta_score, meta_desc = _check_metadata_signals(metadata)
    signals.append({"name": "Metadata authenticity", "description": meta_desc, "confidence": int(meta_score)})
    scores.append(meta_score)
    weights.append(2.0)  # Metadata gets extra weight - camera info is a strong signal

    if not scores:
        scores = [50]
        weights = [1.0]

    # Weighted average
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    ai_probability = int(min(90, max(15, weighted_sum / total_weight)))

    # Derive other probabilities
    manipulation_probability = int(min(85, max(10, ai_probability * 0.6 + 10)))
    authentic_probability = max(0, 100 - ai_probability)

    return {
        "ai_probability": ai_probability,
        "manipulation_probability": manipulation_probability,
        "authentic_probability": authentic_probability,
        "signals": signals,
        "is_fallback": False
    }
