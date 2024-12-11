from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("")
async def health():  # pragma: no cover
    return {"status": "OK"}
