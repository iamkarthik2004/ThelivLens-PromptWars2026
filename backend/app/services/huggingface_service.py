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

async def analyze_with_vision(media: str | Path | None, forensic_results: dict) -> dict | None:
    settings = get_settings()
    if not settings.hf_token or not settings.hf_model_id:
        return None
    try:
        content = [{"type": "text", "text": f"Forensic signals:\n{json.dumps(forensic_results, default=str)}"}]
        if media:
            data = base64.b64encode(Path(media).read_bytes()).decode()
            mime = "image/jpeg" if str(media).lower().endswith((".jpg", ".jpeg")) else "image/png"
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}})
        payload = {"model": settings.hf_model_id, "messages": [{"role": "system", "content": INSTRUCTION}, {"role": "user", "content": content}], "max_tokens": 700, "temperature": 0.2}
        # Keep uploads responsive when the hosted provider is unreachable.
        # A short-lived synchronous client avoids lingering async sockets on restricted networks.
        with httpx.Client(timeout=httpx.Timeout(3.0, connect=0.5), trust_env=False) as client:
            response = client.post("https://router.huggingface.co/v1/chat/completions", headers={"Authorization": f"Bearer {settings.hf_token}"}, json=payload)
        if response.status_code in (401, 403): log.warning("Hugging Face authentication failed"); return None
        if response.status_code == 429: log.warning("Hugging Face rate limited"); return None
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        text = text.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except (httpx.HTTPError, KeyError, ValueError, OSError) as exc:
        log.warning("Hugging Face inference unavailable: %s", exc.__class__.__name__)
        return None
