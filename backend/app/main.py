import time
import uuid
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.auth import get_current_user
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.customers import router as customers_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.cashflow import router as cashflow_router
from app.api.v1.seed import router as seed_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.management import router as management_router
from app.api.v1.phase3 import router as phase3_router
from app.api.v1.settings import router as settings_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration per 04_AUTH_SECURITY.md (strictly explicit origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Centralized error handling per docs/05_API_SPEC.md
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "req_unknown")
    details = []
    for err in exc.errors():
        details.append({
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", "Invalid value"),
            "type": err.get("type"),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request body or parameters could not be validated.",
                "request_id": request_id,
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "req_unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "request_id": request_id,
                "details": [],
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "req_unknown")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request_id,
                "details": [],
            }
        },
    )


# Register API routers
# Public endpoints
app.include_router(health_router)
app.include_router(auth_router)

# Protected domain endpoints (require valid Bearer JWT)
_tenant_dependency = Depends(get_current_user, scope="function")
app.include_router(dashboard_router, dependencies=[_tenant_dependency])
app.include_router(customers_router, dependencies=[_tenant_dependency])
app.include_router(suppliers_router, dependencies=[_tenant_dependency])
app.include_router(transactions_router, dependencies=[_tenant_dependency])
app.include_router(cashflow_router, dependencies=[_tenant_dependency])
app.include_router(seed_router, dependencies=[_tenant_dependency])
app.include_router(expenses_router, dependencies=[_tenant_dependency])
app.include_router(alerts_router, dependencies=[_tenant_dependency])
app.include_router(scenarios_router, dependencies=[_tenant_dependency])
app.include_router(management_router, dependencies=[_tenant_dependency])
app.include_router(phase3_router, dependencies=[_tenant_dependency])
app.include_router(settings_router, dependencies=[_tenant_dependency])
