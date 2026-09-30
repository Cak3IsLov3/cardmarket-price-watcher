from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers tables with SQLModel)
from app.database import create_db_and_tables
from app.routers import watchlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Cardmarket Price Watcher", lifespan=lifespan)
app.include_router(watchlist.router)

from fastapi.responses import RedirectResponse


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")