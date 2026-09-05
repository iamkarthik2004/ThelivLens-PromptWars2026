from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.dependencies import RepositoryDep, StorageDep
from app.schemas import AnalysisResponse, UrlAnalysisRequest
from app.services import create_record, media_kind, read_validated_upload

router = APIRouter(prefix="/analyses", tags=["analyses"])


def response_from_record(record: dict) -> AnalysisResponse:
    return AnalysisResponse.model_validate(record)


@router.post("/upload", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_analysis(
    file: UploadFile = File(description="Image, video, or audio file to inspect"),
    repository: RepositoryDep = None,
    storage: StorageDep = None,
) -> AnalysisResponse:
    try:
        contents, content_type = await read_validated_upload(file, max_bytes=500 * 1024 * 1024)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

    filename = file.filename or "uploaded-media"
    object_key = await storage.put(filename, contents, content_type)
    record = create_record(filename, content_type, media_kind(content_type), object_key, seed=f"{filename}:{len(contents)}")
    return response_from_record(await repository.create(record))


@router.post("/url", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_url(payload: UrlAnalysisRequest, repository: RepositoryDep = None) -> AnalysisResponse:
    host = payload.url.host or "remote-media"
    record = create_record(host, "remote-media", "remote-media", None, seed=str(payload.url))
    return response_from_record(await repository.create(record))


@router.get("/{analysis_id}", response_model=AnalysisResponse, responses={404: {"description": "Analysis not found"}})
async def get_analysis(analysis_id: str, repository: RepositoryDep = None) -> AnalysisResponse:
    record = await repository.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return response_from_record(record)
