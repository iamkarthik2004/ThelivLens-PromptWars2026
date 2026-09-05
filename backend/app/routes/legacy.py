from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app.routes.analysis import ALLOWED, create, response
from app.schemas import AnalysisResponse, UrlAnalysisRequest
router = APIRouter(prefix="/analyses")
@router.post("/upload", response_model=AnalysisResponse, status_code=201)
async def upload(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED: raise HTTPException(422, "Unsupported media type")
    data = await file.read(500 * 1024 * 1024 + 1)
    if len(data) > 500 * 1024 * 1024: raise HTTPException(422, "Files must be 500 MB or smaller.")
    return response(await create(request, file.filename or "uploaded-media", file.content_type, data))
@router.post("/url", response_model=AnalysisResponse, status_code=201)
async def url(payload: UrlAnalysisRequest, request: Request): return response(await create(request, payload.url.host or "remote-media", "image/jpeg", str(payload.url).encode()))
@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_one(analysis_id: str, request: Request):
    x = await request.app.state.repository.get(analysis_id)
    if not x: raise HTTPException(404, "Analysis not found")
    return response(x)
