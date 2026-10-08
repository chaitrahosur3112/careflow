from contextlib import asynccontextmanager

from decouple import config, Csv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ml.overcrowding import OvercrowdingModel
from app.ml.wait_time import WaitTimeModel
from app.routers.predictions import router as predictions_router

ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:8000,http://localhost:5173", cast=Csv()
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load both models once at startup rather than per-request — this is
    # the whole reason the wait-time/overcrowding endpoints stay fast.
    app.state.wait_time_model = WaitTimeModel()
    app.state.overcrowding_model = OvercrowdingModel()
    yield


app = FastAPI(
    title="CareFlow ML Service",
    description="Wait-time prediction, overcrowding-risk forecasting, and staffing recommendations for CareFlow.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Django backend only — never wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(predictions_router)


@app.get("/health")
def health():
    return {"status": "ok"}
