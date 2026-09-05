import json
import logging
from pathlib import Path
import base64
import httpx
from app.core.config import get_settings

log = logging.getLogger(__name__)

INSTRUCTION = """You are the reasoning and explanation engine for ThelivLens, an AI-powered media verification platform.
Analyze the media together with forensic signals. Do not claim absolute certainty or label unusual media fake automatically.
Consider evidence for manipulation and authenticity. Return ONLY valid JSON with keys summary, verdict, confidence, key_evidence, concerns, recommended_verification_steps.
Allowed verdicts: likely_ai_generated, potentially_manipulated, probably_authentic, inconclusive. The assessment is probabilistic."""


def _detect_mime(media_path: Path) -> str:
    suffix = media_path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    return mime_map.get(suffix, "image/jpeg")


async def analyze_with_vision(media: str | Path | None, forensic_results: dict) -> dict | None:
    settings = get_settings()
    if not settings.hf_token or not settings.hf_model_id:
        log.warning("HF token or model ID not configured - skipping vision analysis")
        return None

    media_path = Path(media) if media else None
    content = [{"type": "text", "text": f"Forensic signals from local analysis:\n{json.dumps(forensic_results, default=str)}\n\nPlease analyze this image and determine if it is AI-generated or a real photograph. Consider the forensic signals but make your own assessment based on the visual content."}]

    if media_path and media_path.exists():
        try:
            raw_bytes = media_path.read_bytes()
            data = base64.b64encode(raw_bytes).decode()
            mime = _detect_mime(media_path)
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}})
            log.info("Attached image %s (%d bytes, %s) to vision request", media_path.name, len(raw_bytes), mime)
        except Exception as e:
            log.warning("Failed to read media file %s: %s", media_path, e)

    payload = {
        "model": settings.hf_model_id,
        "messages": [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": content}
        ],
        "max_tokens": 700,
        "temperature": 0.2
    }

    try:
        log.info("Calling HuggingFace model %s ...", settings.hf_model_id)
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0), trust_env=False) as client:
            response = client.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.hf_token}"},
                json=payload
            )

        log.info("HuggingFace response status: %d", response.status_code)

        if response.status_code == 401:
            log.error("HuggingFace auth failed (401). Token may be invalid or expired.")
            return None
        if response.status_code == 403:
            log.error("HuggingFace forbidden (403). Model access may not be granted.")
            return None
        if response.status_code == 429:
            log.warning("HuggingFace rate limited (429). Will retry later.")
            return None
        if response.status_code == 503:
            log.warning("HuggingFace model loading (503). Please wait.")
            return None

        response.raise_for_status()
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        text = text.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(text)

        if isinstance(parsed, dict) and "verdict" in parsed:
            log.info("HuggingFace verdict: %s (confidence: %s)", parsed.get("verdict"), parsed.get("confidence"))
            return parsed
        else:
            log.warning("HuggingFace returned invalid structure: %s", text[:200])
            return None

    except httpx.TimeoutException as exc:
        log.error("HuggingFace timeout after %.1fs: %s", 60.0, exc)
        return None
    except httpx.HTTPError as exc:
        log.error("HuggingFace HTTP error: %s", exc)
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        log.error("HuggingFace response parse error: %s", exc)
        return None
    except Exception as exc:
        log.error("Unexpected HuggingFace error: %s: %s", type(exc).__name__, exc)
        return None
