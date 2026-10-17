import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.brand_profile_routes import router as brand_profile_router
from app.api.notification_routes import router as notification_router
from app.api.on_demand_routes import router as on_demand_router
from app.api.pillar_routes import router as pillar_router
from app.api.product_routes import router as product_router
from app.api.reference_image_routes import router as reference_image_router
from app.api.routes import router
from app.core.config import get_settings
from app.services.storage import close_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="Brand Manager API",
    version="0.1.0",
    description="Brands, daily image generation, and approval workflow",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def _shutdown() -> None:
    await close_client()


app.include_router(router)
app.include_router(brand_profile_router)
app.include_router(product_router)
app.include_router(pillar_router)
app.include_router(reference_image_router)
app.include_router(notification_router)
app.include_router(on_demand_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "brand-manager-api", "env": settings.app_env}
