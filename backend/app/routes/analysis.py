import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app.core.config import get_settings
from app.schemas import AnalysisResponse, ClaimRequest, CopilotRequest, UrlAnalysisRequest
from app.services.detector import detect_media
from app.services.media_analysis import extract_metadata
from app.services.huggingface_service import analyze_with_vision
from app.services.source_trace import source_trace_fallback
from app.services.storage import LocalObjectStorage

router = APIRouter(prefix="/analyze", tags=["analysis"])
ALLOWED = {"image/jpeg":"image","image/png":"image","image/webp":"image","video/mp4":"video","video/quicktime":"video","video/webm":"video","audio/mpeg":"audio","audio/wav":"audio","audio/x-wav":"audio","audio/mp4":"audio"}
def response(r):
    m=r["report"]["metrics"]; return {**r,"id":r["analysis_id"],"name":r["filename"],"type":r["content_type"],"media_kind":r["media_type"],"overall_verdict":r["overall_verdict"],"confidence":r["confidence"],"ai_probability":m["ai_generated"],"manipulation_probability":m["manipulated"],"authentic_probability":m["authentic"],"evidence_data":r["report"]["evidence"]}
async def create(request, filename, ctype, data):
    kind=ALLOWED[ctype]; digest=hashlib.sha256(data).hexdigest(); path=await LocalObjectStorage().put(filename,data,ctype); metadata=await extract_metadata(path,kind); forensic=detect_media(path,kind,metadata); explanation=await analyze_with_vision(path,forensic); score=forensic["ai_probability"]
    verdict=(explanation or {}).get("verdict") or ("likely_ai_generated" if score>=75 else "potentially_manipulated" if score>=55 else "inconclusive"); confidence=int((explanation or {}).get("confidence",score)); evidence=[{"title":s["name"],"description":s["description"],"severity":"Medium","confidence":s.get("confidence",35),"icon":"Search"} for s in forensic["signals"]]; trace=source_trace_fallback()
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
async def copilot(payload:CopilotRequest): return {"answer":"Use the strongest listed evidence and corroborate the earliest source. This assessment is probabilistic.","question":payload.question}
