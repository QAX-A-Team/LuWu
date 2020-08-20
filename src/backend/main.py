import logging
import time
import traceback

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from api.api_v1.api import api_router
from core import config
from db.session import Session
from schemas.base import BaseFailedResponseModel

app = FastAPI(
    title=config.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json"
)
app.include_router(api_router, prefix=config.API_V1_STR)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    failed_res = BaseFailedResponseModel(errors=[exc.detail]).dict()
    status_code = exc.status_code or status.HTTP_400_BAD_REQUEST
    return JSONResponse(failed_res, status_code=status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    failed_res = BaseFailedResponseModel(errors=exc.errors()).dict()
    return JSONResponse(failed_res, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logging.warning(traceback.format_exc())
        exc_data = {
            'msg': "Internal server error",
            'detail': str(e)
        }
        failed_res = BaseFailedResponseModel(errors=[exc_data]).dict()
        return JSONResponse(failed_res, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = Session()
    response = await call_next(request)
    request.state.db.close()
    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Set all CORS enabled origins
origins = []
if config.BACKEND_CORS_ORIGINS:
    origins_raw = config.BACKEND_CORS_ORIGINS.split(",")
    for origin in origins_raw:
        use_origin = origin.strip()
        origins.append(use_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
