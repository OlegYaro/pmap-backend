import taskiq_fastapi
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers.router import api_router
from clients.extraction import ExtractionError
from core import setup_logging
from jobs.broker import broker

setup_logging()

app = FastAPI(title="PMAP Backend")
taskiq_fastapi.init(broker, "api.main:app")

app.include_router(api_router)


@app.exception_handler(ExtractionError)
async def extraction_error_handler(_: Request, error: ExtractionError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
