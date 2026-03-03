import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db import Base, engine


logger = logging.getLogger("app")
settings = get_settings()


def init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def create_app() -> FastAPI:
    init_logging()

    app = FastAPI(
        title=settings.app_name,
        description="用于管理文档及分片的基础服务，所有接口说明均为中文。",
        version="1.0.0",
        docs_url="/接口文档",
        redoc_url="/接口说明",
        openapi_url="/openapi.json",
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表已初始化")

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info("收到请求 request_id=%s path=%s", request_id, request.url.path)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    @app.get(
        "/",
        include_in_schema=False,
    )
    async def root():
        return RedirectResponse(url="/接口文档")

    app.include_router(api_router)

    return app


app = create_app()

