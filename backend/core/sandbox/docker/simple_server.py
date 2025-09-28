#!/usr/bin/env python3
"""
Simple static file server for workspace files
Serves files from /workspace directory on port 8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from pathlib import Path

# Ensure we're serving from the /workspace directory
workspace_dir = "/workspace"

app = FastAPI(title="Workspace File Server")

# Create workspace directory if it doesn't exist
os.makedirs(workspace_dir, exist_ok=True)

# Serve files from workspace directory with proper path handling
@app.get("/workspace/{file_path:path}")
async def serve_workspace_file(file_path: str):
    """Serve files from workspace directory with proper path handling"""
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "workspace_dir": workspace_dir}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Workspace File Server", "workspace_dir": workspace_dir}

if __name__ == '__main__':
    print(f"Starting simple workspace server on port 8080, serving files from: {workspace_dir}")
    uvicorn.run(app, host="0.0.0.0", port=8080)
