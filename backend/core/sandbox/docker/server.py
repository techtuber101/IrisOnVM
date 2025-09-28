from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
import logging
import sys
from pathlib import Path

# Configure logging early
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Import routers with error handling
logger.info("Importing routers...")
try:
    from html_to_pdf_router import router as pdf_router
    PDF_ROUTER_AVAILABLE = True
    logger.info("✓ PDF router imported successfully")
except ImportError as e:
    logger.warning(f"✗ PDF router not available: {e}")
    logger.warning(f"PDF router import error details: {type(e).__name__}: {str(e)}")
    PDF_ROUTER_AVAILABLE = False
except Exception as e:
    logger.error(f"✗ PDF router failed to import: {e}")
    logger.error(f"PDF router error details: {type(e).__name__}: {str(e)}")
    PDF_ROUTER_AVAILABLE = False

try:
    from visual_html_editor_router import router as editor_router
    EDITOR_ROUTER_AVAILABLE = True
    logger.info("✓ Editor router imported successfully")
except ImportError as e:
    logger.warning(f"✗ Editor router not available: {e}")
    logger.warning(f"Editor router import error details: {type(e).__name__}: {str(e)}")
    EDITOR_ROUTER_AVAILABLE = False
except Exception as e:
    logger.error(f"✗ Editor router failed to import: {e}")
    logger.error(f"Editor router error details: {type(e).__name__}: {str(e)}")
    EDITOR_ROUTER_AVAILABLE = False

try:
    from html_to_pptx_router import router as pptx_router
    PPTX_ROUTER_AVAILABLE = True
    logger.info("✓ PPTX router imported successfully")
except ImportError as e:
    logger.warning(f"✗ PPTX router not available: {e}")
    logger.warning(f"PPTX router import error details: {type(e).__name__}: {str(e)}")
    PPTX_ROUTER_AVAILABLE = False
except Exception as e:
    logger.error(f"✗ PPTX router failed to import: {e}")
    logger.error(f"PPTX router error details: {type(e).__name__}: {str(e)}")
    PPTX_ROUTER_AVAILABLE = False

try:
    from html_to_docx_router import router as docx_router
    DOCX_ROUTER_AVAILABLE = True
    logger.info("✓ DOCX router imported successfully")
except ImportError as e:
    logger.warning(f"✗ DOCX router not available: {e}")
    logger.warning(f"DOCX router import error details: {type(e).__name__}: {str(e)}")
    DOCX_ROUTER_AVAILABLE = False
except Exception as e:
    logger.error(f"✗ DOCX router failed to import: {e}")
    logger.error(f"DOCX router error details: {type(e).__name__}: {str(e)}")
    DOCX_ROUTER_AVAILABLE = False

# Ensure we're serving from the /workspace directory
workspace_dir = "/workspace"
logger.info(f"Workspace directory set to: {workspace_dir}")

class WorkspaceDirMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if workspace directory exists and recreate if deleted
        if not os.path.exists(workspace_dir):
            logger.warning(f"Workspace directory {workspace_dir} not found, recreating...")
            os.makedirs(workspace_dir, exist_ok=True)
            logger.info(f"Created workspace directory: {workspace_dir}")
        return await call_next(request)

logger.info("Creating FastAPI app...")
app = FastAPI(title="Workspace Server", version="1.0.0")
app.add_middleware(WorkspaceDirMiddleware)
logger.info("✓ FastAPI app created and middleware added")

# Include routers if available
logger.info("Including routers...")
if PDF_ROUTER_AVAILABLE:
    app.include_router(pdf_router)
    logger.info("✓ PDF router included")
if EDITOR_ROUTER_AVAILABLE:
    app.include_router(editor_router)
    logger.info("✓ Editor router included")
if PPTX_ROUTER_AVAILABLE:
    app.include_router(pptx_router)
    logger.info("✓ PPTX router included")
if DOCX_ROUTER_AVAILABLE:
    app.include_router(docx_router)
    logger.info("✓ DOCX router included")

# Create output directory for generated PDFs (needed by PDF router)
logger.info("Setting up directories...")
output_dir = Path("generated_pdfs")
output_dir.mkdir(exist_ok=True)
logger.info(f"✓ Created output directory: {output_dir}")

# Mount static files for PDF downloads
app.mount("/downloads", StaticFiles(directory=str(output_dir)), name="downloads")
logger.info("✓ Mounted downloads directory")

# Initial directory creation
os.makedirs(workspace_dir, exist_ok=True)
logger.info(f"✓ Created workspace directory: {workspace_dir}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running"""
    return {
        "status": "ok", 
        "workspace_dir": workspace_dir,
        "workspace_exists": os.path.exists(workspace_dir),
        "routers": {
            "pdf": PDF_ROUTER_AVAILABLE,
            "editor": EDITOR_ROUTER_AVAILABLE,
            "pptx": PPTX_ROUTER_AVAILABLE,
            "docx": DOCX_ROUTER_AVAILABLE
        }
    }

# Add visual HTML editor root endpoint
@app.get("/editor")
async def list_html_files():
    """List all HTML files in the workspace for easy access"""
    from fastapi.responses import HTMLResponse
    try:
        html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
        
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Visual HTML Editor</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, system-ui, sans-serif;
                    background: white;
                    color: black;
                    line-height: 1.5;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 32px;
                    border-bottom: 1px solid #e4e4e7;
                    padding-bottom: 24px;
                }
                .header h1 {
                    font-size: 24px;
                    font-weight: 600;
                    letter-spacing: -0.025em;
                    margin-bottom: 8px;
                    color: #09090b;
                }
                .header p {
                    font-size: 14px;
                    color: #71717a;
                    font-weight: 400;
                }
                .file-list {
                    border: 1px solid #e4e4e7;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .file-item {
                    padding: 16px 20px;
                    border-bottom: 1px solid #e4e4e7;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    transition: background-color 0.15s ease;
                }
                .file-item:hover {
                    background: #f4f4f5;
                }
                .file-item:last-child {
                    border-bottom: none;
                }
                .file-name {
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                    font-size: 14px;
                    font-weight: 500;
                    color: black;
                }
                .file-actions {
                    display: flex;
                    gap: 12px;
                }
                .btn {
                    padding: 8px 16px;
                    text-decoration: none;
                    font-size: 13px;
                    font-weight: 500;
                    border: 1px solid #e4e4e7;
                    color: #09090b;
                    background: white;
                    transition: all 0.15s ease;
                    text-align: center;
                    min-width: 60px;
                    border-radius: 6px;
                }
                .btn:hover {
                    background: #f4f4f5;
                    border-color: #d4d4d8;
                }
                .btn-edit {
                    background: #09090b;
                    color: white;
                    border-color: #09090b;
                }
                .btn-edit:hover {
                    background: #18181b;
                    border-color: #18181b;
                }
                .empty-state {
                    text-align: center;
                    padding: 64px 20px;
                    color: #71717a;
                    border: 1px solid #e4e4e7;
                    border-radius: 8px;
                }
                .empty-state h3 {
                    font-size: 16px;
                    font-weight: 500;
                    margin-bottom: 8px;
                    color: #09090b;
                }
                .info {
                    margin-top: 32px;
                    padding: 20px;
                    background: #fafafa;
                    border: 1px solid #e4e4e7;
                    border-radius: 8px;
                }
                .info h3 {
                    font-size: 16px;
                    font-weight: 500;
                    margin-bottom: 12px;
                }
                .info-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                .info-item {
                    font-size: 14px;
                    line-height: 1.4;
                }
                .info-item strong {
                    font-weight: 500;
                }
                @media (max-width: 600px) {
                    .info-grid {
                        grid-template-columns: 1fr;
                    }
                    .file-item {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 12px;
                    }
                    .file-actions {
                        width: 100%;
                        justify-content: flex-end;
                    }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Visual HTML Editor</h1>
                <p>Click-to-edit any HTML file with live preview</p>
            </div>
            
            <div class="file-list">
        """
        
        if html_files:
            for file in sorted(html_files):
                html_content += f"""
                <div class="file-item">
                    <div class="file-name">{file}</div>
                    <div class="file-actions">
                        <a href="/{file}" class="btn" target="_blank">View</a>
                        <a href="/api/html/{file}/editor" class="btn btn-edit" target="_blank">Edit</a>
                    </div>
                </div>
                """
        else:
            html_content += """
            <div class="empty-state">
                <h3>No files found</h3>
                <p>Add .html files to this directory to start editing</p>
            </div>
            """
        
        html_content += """
            </div>
            
            <div class="info">
                <h3>How to use</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Edit text:</strong> Hover over any text and click the edit icon
                    </div>
                    <div class="info-item">
                        <strong>Delete elements:</strong> Click the trash icon to remove content
                    </div>
                    <div class="info-item">
                        <strong>Save changes:</strong> Press Ctrl+Enter or click Save
                    </div>
                    <div class="info-item">
                        <strong>Cancel editing:</strong> Press Escape or click Cancel
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Error listing HTML files: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

# Serve HTML files directly at root level
@app.get("/{file_name}")
async def serve_html_file(file_name: str):
    """Serve HTML files directly for viewing"""
    from fastapi import HTTPException
    from fastapi.responses import HTMLResponse
    
    if not file_name.endswith('.html'):
        raise HTTPException(status_code=404, detail="File must be .html")
    
    file_path = os.path.join(workspace_dir, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return HTMLResponse(content=content)

# Serve files from workspace directory with proper path handling
@app.get("/workspace/{file_path:path}")
async def serve_workspace_file(file_path: str):
    """Serve files from workspace directory with proper path handling"""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse, HTMLResponse
    
    full_path = os.path.join(workspace_dir, file_path)
    
    # Security check - ensure path is within workspace
    if not os.path.abspath(full_path).startswith(os.path.abspath(workspace_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    if os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Directory listing not allowed")
    
    # Serve HTML files with proper content type
    if file_path.endswith('.html'):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    
    # Serve other files
    return FileResponse(full_path)

app.mount('/', StaticFiles(directory=workspace_dir, html=True), name='site')
logger.info("✓ Mounted static files directory")

# This is needed for the import string approach with uvicorn
if __name__ == '__main__':
    import logging
    import sys
    import traceback
    
    # Configure comprehensive logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("STARTING WORKSPACE SERVER")
        logger.info("=" * 60)
        logger.info(f"Workspace directory: {workspace_dir}")
        logger.info(f"Workspace exists: {os.path.exists(workspace_dir)}")
        logger.info(f"Workspace is directory: {os.path.isdir(workspace_dir)}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"FastAPI app object: {app}")
        logger.info(f"App routes: {[route.path for route in app.routes]}")
        
        # Test workspace directory
        if os.path.exists(workspace_dir):
            try:
                files = os.listdir(workspace_dir)
                logger.info(f"Workspace contents: {files[:10]}...")  # Show first 10 files
            except Exception as e:
                logger.error(f"Error listing workspace: {e}")
        else:
            logger.warning(f"Workspace directory {workspace_dir} does not exist, creating...")
            os.makedirs(workspace_dir, exist_ok=True)
            logger.info(f"Created workspace directory: {workspace_dir}")
        
        logger.info("Starting uvicorn server...")
        logger.info(f"Host: 0.0.0.0, Port: 8080, Reload: True")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8080, 
            reload=True,
            log_level="debug",
            access_log=True
        )
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("CRITICAL ERROR STARTING SERVER")
        logger.error("=" * 60)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        sys.exit(1) 