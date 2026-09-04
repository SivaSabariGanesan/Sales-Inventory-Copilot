from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Retail Sales & Inventory Copilot API & Web Server",
    version="0.1.0",
)

# Minimum health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# Static files and SPA serving configuration
frontend_dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"

if frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
    # Mount assets directory if available
    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve SPA routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist_dir / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist_dir / "index.html")
else:
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
                        <p>Backend server is running on port 8000.</p>
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
