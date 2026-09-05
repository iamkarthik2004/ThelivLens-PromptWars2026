from typing import Annotated

from fastapi import Depends, Request

from app.services import InMemoryRepository


async def get_repository(request: Request):
    return request.app.state.repository


async def get_storage(request: Request):
    return request.app.state.storage


RepositoryDep = Annotated[InMemoryRepository, Depends(get_repository)]
StorageDep = Annotated[object, Depends(get_storage)]
