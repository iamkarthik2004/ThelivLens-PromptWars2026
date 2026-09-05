from typing import Annotated

from fastapi import Depends, Request

from app.database import InMemoryRepository


async def get_repository(request: Request):
    return request.app.state.repository


RepositoryDep = Annotated[InMemoryRepository, Depends(get_repository)]
