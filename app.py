import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from starlette.types import ASGIApp, Scope, Receive, Send

from backend.config import settings
from backend.database.schema import init_db
from backend.routes.auth import router as auth_router
from backend.routes.inventory import router as inventory_router
from backend.routes.sales import router as sales_router
from backend.routes.copilot import router as copilot_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.products import router as products_router
from backend.routes.stores import router as stores_router
from backend.routes.settings import router as settings_router
from backend.routes.data_import import router as import_router
from backend.routes.audit import router as audit_router
from backend.routes.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Retail Sales & Inventory Copilot API & Web Server",
    version="0.1.0",
    lifespan=lifespan,
)

# Eagerly initialize SQLite schema and tables
try:
    init_db(seed=True)
except Exception as e:
    print(f"Startup DB init notice: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def normalize_vercel_api_paths(request, call_next):
    # Handle all Vercel serverless routing variations
    path = request.url.path
    
    # Strip serverless file references if injected into path
    if path.startswith("/api/index.py"):
        path = path.replace("/api/index.py", "", 1) or "/"
    elif path.startswith("/api/index"):
        path = path.replace("/api/index", "", 1) or "/"

    api_prefixes = (
        "dashboard", "inventory", "sales", "copilot", "recommendations",
        "auth", "health", "products", "stores", "settings", "import",
        "audit", "usage", "analytics"
    )
    
    # Restore /api prefix if stripped
    if not path.startswith("/api"):
        clean_path = path.lstrip("/")
        for prefix in api_prefixes:
            if clean_path == prefix or clean_path.startswith(prefix + "/"):
                path = "/api/" + clean_path
                break

    request.scope["path"] = path
    return await call_next(request)

# API routes
app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(copilot_router)
app.include_router(recommendations_router)
app.include_router(dashboard_router)
app.include_router(products_router)
app.include_router(stores_router)
app.include_router(settings_router)
app.include_router(import_router)
app.include_router(audit_router)
app.include_router(analytics_router)


# Health check endpoint
@app.get("/api")
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "database": "sqlite",
        "db_path": str(settings.DB_PATH.name),
    }


# Static files and SPA serving configuration (Local development only; Vercel handles static assets at the CDN edge)
is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))
frontend_dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"

if not is_vercel and frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
    # Mount assets directory if available
    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve SPA routes for local standalone server
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail=f"API endpoint '/{full_path}' not found")
        file_path = frontend_dist_dir / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist_dir / "index.html")
elif not is_vercel:
    @app.get("/")
    async def root():
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Retail Sales & Inventory Copilot</title>
                    <style>
                        body { font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f8fafc; color: #1e293b; }
                        .card { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); max-width: 500px; text-align: center; }
                        h1 { color: #0f172a; margin-bottom: 0.5rem; font-size: 1.5rem; }
                        p { color: #64748b; line-height: 1.6; }
                        code { background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>Retail Sales & Inventory Copilot</h1>
                        <p>Backend server & SQLite database running on port 8000.</p>
                        <p>To serve the React UI, run <code>npm run build</code> in the <code>frontend/</code> directory.</p>
                    </div>
                </body>
            </html>
            """,
            status_code=200,
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
