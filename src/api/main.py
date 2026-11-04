import taskiq_fastapi
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from api.routers.router import api_router
from core import setup_logging
from integrations.extraction import ExtractionError
from jobs.broker import broker

setup_logging()

# The API Gateway checks the token; this only adds the Authorize button to Swagger.
app = FastAPI(
    title="PMAP Backend",
    dependencies=[Depends(HTTPBearer(auto_error=False))],
    swagger_ui_parameters={"persistAuthorization": True},
)
taskiq_fastapi.init(broker, "api.main:app")

app.include_router(api_router)


@app.exception_handler(ExtractionError)
async def extraction_error_handler(_: Request, error: ExtractionError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})
