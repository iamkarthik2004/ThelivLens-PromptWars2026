import hashlib
import logging
from datetime import datetime, timezone
from uuid import uuid4
import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app.core.config import get_settings

log = logging.getLogger(__name__)
from app.schemas import AnalysisResponse, ClaimRequest, CopilotRequest, UrlAnalysisRequest
from app.services.detector import detect_media
from app.services.media_analysis import extract_metadata
from app.services.huggingface_service import analyze_with_vision
from app.services.source_trace import source_trace_fallback, source_trace_from_metadata
from app.services.storage import LocalObjectStorage

router = APIRouter(prefix="/analyze", tags=["analysis"])
ALLOWED = {"image/jpeg":"image","image/png":"image","image/webp":"image","video/mp4":"video","video/quicktime":"video","video/webm":"video","audio/mpeg":"audio","audio/wav":"audio","audio/x-wav":"audio","audio/mp4":"audio"}
def response(r):
    m=r["report"]["metrics"]; return {**r,"id":r["analysis_id"],"name":r["filename"],"type":r["content_type"],"media_kind":r["media_type"],"overall_verdict":r["overall_verdict"],"confidence":r["confidence"],"ai_probability":m["ai_generated"],"manipulation_probability":m["manipulated"],"authentic_probability":m["authentic"],"evidence_data":r["report"]["evidence"]}
async def create(request, filename, ctype, data):
    kind=ALLOWED[ctype]; digest=hashlib.sha256(data).hexdigest(); path=await LocalObjectStorage().put(filename,data,ctype); metadata=await extract_metadata(path,kind); forensic=detect_media(path,kind,metadata); explanation=await analyze_with_vision(path,forensic); score=forensic["ai_probability"]
    verdict=(explanation or {}).get("verdict") or ("likely_ai_generated" if score>=75 else "potentially_manipulated" if score>=55 else "inconclusive"); confidence=int((explanation or {}).get("confidence",score)); evidence=[{"title":s["name"],"description":s["description"],"severity":"High" if s.get("confidence",0)>=75 else "Medium" if s.get("confidence",0)>=50 else "Low","confidence":s.get("confidence",35),"icon":"Search"} for s in forensic["signals"]]; trace=source_trace_from_metadata(metadata)
    report={"verdict":verdict.replace("_"," ").title(),"confidence":confidence,"metrics":{"ai_generated":forensic["ai_probability"],"manipulated":forensic["manipulation_probability"],"authentic":forensic["authentic_probability"]},"evidence":evidence,"source_events":trace,"disclaimer":"AI analysis is probabilistic and is not definitive proof of authenticity or manipulation.","ai_explanation":explanation or {"summary":"Local forensic signals returned; Hugging Face reasoning was unavailable.","key_evidence":[],"concerns":[],"recommended_verification_steps":["Verify the earliest source and original file."]}}
    return await request.app.state.repository.create({"analysis_id":str(uuid4()),"filename":filename,"content_type":ctype,"media_type":kind,"file_hash":digest,"status":"completed","overall_verdict":verdict,"confidence":confidence,"metadata":metadata,"report":report,"source_trace":trace,"created_at":datetime.now(timezone.utc),"object_key":path})
@router.post("/upload",response_model=AnalysisResponse,status_code=201)
async def upload(request:Request,file:UploadFile=File(...)):
    if file.content_type not in ALLOWED: raise HTTPException(422,"Unsupported media type")
    data=await file.read(get_settings().upload_limit_bytes+1)
    if not data or len(data)>get_settings().upload_limit_bytes: raise HTTPException(422,"Files must be 500 MB or smaller.")
    return response(await create(request,file.filename or "uploaded-media",file.content_type,data))
@router.post("/url",response_model=AnalysisResponse,status_code=201)
async def url(payload:UrlAnalysisRequest,request:Request): return response(await create(request,payload.url.host or "remote-media","image/jpeg",("remote:"+str(payload.url)).encode()))
@router.post("/claim")
async def claim(payload:ClaimRequest): return {"claim":payload.claim,"assessment":"Inconclusive without source media","confidence":0}
@router.get("")
async def recent(request:Request): return [response(x) for x in await request.app.state.repository.list_recent()]
@router.get("/{analysis_id}",response_model=AnalysisResponse)
async def get_one(analysis_id:str,request:Request):
    x=await request.app.state.repository.get(analysis_id)
    if not x: raise HTTPException(404,"Analysis not found")
    return response(x)
@router.get("/{analysis_id}/source-trace")
async def trace(analysis_id:str,request:Request):
    x=await request.app.state.repository.get(analysis_id)
    if not x: raise HTTPException(404,"Analysis not found")
    return x["source_trace"]
@router.delete("/{analysis_id}")
async def remove(analysis_id:str,request:Request):
    if not await request.app.state.repository.delete(analysis_id): raise HTTPException(404,"Analysis not found")
    return {"deleted":True}
@router.post("/copilot")
async def copilot(payload:CopilotRequest, request: Request):
    context = payload.analysis_context
    context_str = ""
    if context:
        report = context.get("report", {})
        metrics = report.get("metrics", {})
        evidence = report.get("evidence", [])
        context_str = f"\nAnalysis context:\n- Verdict: {context.get('overall_verdict', 'Unknown')}\n- Confidence: {context.get('confidence', 'Unknown')}%\n- AI Probability: {metrics.get('ai_generated', 'Unknown')}%\n- Manipulation Probability: {metrics.get('manipulated', 'Unknown')}%\n- Evidence signals: {', '.join(e.get('title', '') for e in evidence[:5])}\n"
    answer = await _copilot_llm(payload.question, context_str)
    return {"answer": answer, "question": payload.question}


async def _copilot_llm(question: str, context: str = "") -> str:
    settings = get_settings()
    if not settings.hf_token or not settings.hf_model_id:
        return _fallback_answer(question)
    try:
        system_prompt = """You are ThelivLens Copilot, an AI assistant that helps users understand media verification results.
Answer questions about analysis results clearly and concisely. Be honest about uncertainty.
Always recommend independent verification. Never claim absolute certainty about media authenticity.
Keep responses under 3 sentences unless more detail is needed."""
        user_msg = f"{context}\n\nUser question: {question}"
        payload = {
            "model": settings.hf_model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }
        with httpx.Client(timeout=httpx.Timeout(5.0, connect=1.0), trust_env=False) as client:
            response = client.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.hf_token}"},
                json=payload
            )
        if response.status_code in (401, 403, 429):
            return _fallback_answer(question)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return _fallback_answer(question)


def _fallback_answer(question: str) -> str:
    q = question.lower()
    if "trust" in q:
        return "No analysis can guarantee authenticity. Corroborate the strongest evidence signals with an independent source before trusting or sharing this media."
    if "flag" in q or "why" in q:
        return "The system detected multiple forensic signals that deviate from typical camera-captured content. The strongest indicators are checked in the Evidence section of the report."
    if "verify" in q or "next" in q:
        return "Find the earliest known upload of this media, compare it against reputable coverage, and request the original unmodified file whenever possible."
    if "ai" in q or "generated" in q:
        return "The AI probability score reflects the strength of synthetic-media indicators. A high score means multiple signals suggest AI generation, but it is not proof."
    return "Use the strongest listed evidence and corroborate the earliest source. This assessment is probabilistic and should be verified independently."
