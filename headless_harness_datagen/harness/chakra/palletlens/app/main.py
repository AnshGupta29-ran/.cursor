"""PalletLens application assembly: middleware, auth, error handling, startup."""
from __future__ import annotations

import hmac
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .db import make_session_factory
from .errors import ApiError, api_error_handler, error_body
from .logging_config import configure_logging, get_logger
from .mapping import load_category_map
from .profiles import load_profiles
from .routes import router
from .service import PredictionService, UnavailableClassifier, build_default_classifier

DESCRIPTION = """Intake triage vision API for electronics-reuse and refurbishment co-ops.

Volunteers photograph donated hardware at the intake dock; PalletLens runs a
pretrained ImageNet classifier (CPU-only), maps labels through a versioned
refurb-category table, applies a named **threshold profile**, and either
auto-routes the item (bench test / parts harvest / certified recycle) or parks
it in the **review queue** for a coordinator. Every prediction is persisted
with model version, category-map version, latency, and image hash for audit.

All endpoints accept an optional `X-API-Key` header — required only when the
server is started with `API_KEY` set.
"""


def create_app(
    settings: Settings | None = None,
    classifier=None,  # tests inject FakeClassifier here
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger = get_logger()

    app = FastAPI(
        title="PalletLens",
        description=DESCRIPTION,
        version="1.0.0",
        docs_url="/docs",
    )

    category_map = load_category_map(settings.category_map_path)
    profiles = load_profiles(settings.profiles_path)
    session_factory = make_session_factory(settings.database_url)

    if classifier is None:
        try:
            classifier = build_default_classifier(settings)
            logger.info("model loaded", extra={
                "model_name": settings.model_name, "weights_enum": settings.weights_enum,
            })
        except Exception as exc:
            # Fail fast is documented in the log; service stays up with
            # model_loaded=false so /health keeps reporting and requests get 503.
            logger.error("model load failed at startup", extra={"error": str(exc)})
            classifier = UnavailableClassifier(
                settings.model_name, settings.weights_enum, str(exc)
            )

    app.state.service = PredictionService(
        settings=settings,
        classifier=classifier,
        category_map=category_map,
        profiles=profiles,
        session_factory=session_factory,
    )
    app.state.settings = settings

    @app.middleware("http")
    async def request_id_and_auth(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())

        # Optional API-key auth (constant-time compare). Open dev mode when unset.
        if settings.api_key and request.url.path.startswith("/v1/"):
            provided = request.headers.get("X-API-Key", "")
            if not hmac.compare_digest(provided.encode(), settings.api_key.encode()):
                return JSONResponse(
                    status_code=401,
                    content=error_body(
                        "unauthorized", "Missing or invalid X-API-Key header.",
                        request.state.request_id,
                    ),
                )

        try:
            return await call_next(request)
        except ApiError as exc:
            return await api_error_handler(request, exc)
        except Exception:
            logger.exception("unhandled error", extra={
                "request_id": request.state.request_id, "path": request.url.path,
            })
            return JSONResponse(
                status_code=500,
                content=error_body(
                    "internal_error", "An unexpected error occurred.",
                    request.state.request_id,
                ),
            )

    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(router)
    return app


app = create_app()
