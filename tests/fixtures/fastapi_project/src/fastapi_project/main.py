from fastapi import APIRouter, FastAPI

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app = FastAPI()
app.include_router(router)
