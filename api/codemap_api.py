"""
REST API endpoints for codemap generation.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from api.codemap.models import (
    CodemapGenerateRequest,
    CodemapGenerateResponse,
    Codemap,
    CodemapStatus,
)
from api.codemap.engine import CodemapEngine
from api.codemap.storage import CodemapStorage
from api.codemap.utils.security import safe_log_request, redact_sensitive_data
from api.codemap.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/codemap", tags=["codemap"])


class CodemapListItem(BaseModel):
    """Codemap list item for API responses"""
    id: str
    title: str
    query: str
    repo_url: str
    repo_owner: str
    repo_name: str
    status: str
    created_at: str
    is_public: bool


@router.post("/generate", response_model=CodemapGenerateResponse)
async def generate_codemap(http_request: Request, request: CodemapGenerateRequest):
    """
    Generate a new codemap for a repository.
    
    This endpoint starts synchronous generation and returns the completed codemap ID.
    For real-time progress updates, use the WebSocket endpoint instead.
    
    Args:
        http_request: FastAPI request object
        request: Generation request with query and options
        
    Returns:
        Response with codemap ID and status
    """
    # Check rate limit
    check_rate_limit(http_request, "generate")
    
    try:
        # Log request with sensitive data redacted
        safe_log_request(
            request.model_dump(exclude={'token'}),
            f"Generating codemap for {request.repo_url}"
        )
        
        engine = CodemapEngine(
            provider=request.provider or "google",
            model=request.model
        )
        
        codemap = await engine.generate(request)
        
        return CodemapGenerateResponse(
            codemap_id=codemap.id,
            status=codemap.status,
            message="Codemap generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating codemap: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate codemap: {str(e)}"
        )


@router.get("/{codemap_id}", response_model=Codemap)
async def get_codemap(http_request: Request, codemap_id: str):
    """
    Retrieve a saved codemap by ID.
    
    Args:
        http_request: FastAPI request object
        codemap_id: The codemap ID
        
    Returns:
        The complete codemap object
    """
    check_rate_limit(http_request, "get")
    
    storage = CodemapStorage()
    codemap = await storage.load(codemap_id)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    return codemap


@router.delete("/{codemap_id}")
async def delete_codemap(codemap_id: str):
    """
    Delete a codemap.
    
    Args:
        codemap_id: The codemap ID
        
    Returns:
        Success message
    """
    storage = CodemapStorage()
    success = await storage.delete(codemap_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    return {"message": f"Codemap {codemap_id} deleted successfully"}


@router.get("/list/all", response_model=List[CodemapListItem])
async def list_codemaps(
    http_request: Request,
    repo_url: Optional[str] = Query(None, description="Filter by repository URL"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    List saved codemaps.
    
    Args:
        http_request: FastAPI request object
        repo_url: Optional filter by repository URL
        limit: Maximum number of results
        
    Returns:
        List of codemap metadata
    """
    check_rate_limit(http_request, "list")
    
    storage = CodemapStorage()
    codemaps = await storage.list_codemaps(repo_url=repo_url, limit=limit)
    
    return [
        CodemapListItem(
            id=cm.get("id", ""),
            title=cm.get("title", ""),
            query=cm.get("query", ""),
            repo_url=cm.get("repo_url", ""),
            repo_owner=cm.get("repo_owner", ""),
            repo_name=cm.get("repo_name", ""),
            status=cm.get("status", "unknown"),
            created_at=cm.get("created_at", ""),
            is_public=cm.get("is_public", False)
        )
        for cm in codemaps
    ]


@router.get("/repo/{owner}/{repo}", response_model=List[CodemapListItem])
async def get_repo_codemaps(
    owner: str,
    repo: str,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get codemaps for a specific repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        limit: Maximum results
        
    Returns:
        List of codemap metadata for the repository
    """
    storage = CodemapStorage()
    codemaps = await storage.get_by_repo(owner, repo, limit)
    
    return [
        CodemapListItem(
            id=cm.get("id", ""),
            title=cm.get("title", ""),
            query=cm.get("query", ""),
            repo_url=cm.get("repo_url", ""),
            repo_owner=cm.get("repo_owner", ""),
            repo_name=cm.get("repo_name", ""),
            status=cm.get("status", "unknown"),
            created_at=cm.get("created_at", ""),
            is_public=cm.get("is_public", False)
        )
        for cm in codemaps
    ]


@router.post("/{codemap_id}/share")
async def share_codemap(http_request: Request, codemap_id: str):
    """
    Generate a share token for a codemap.
    
    Args:
        http_request: FastAPI request object
        codemap_id: The codemap ID
        
    Returns:
        Share token and URL
    """
    import uuid
    
    check_rate_limit(http_request, "share")
    
    storage = CodemapStorage()
    codemap = await storage.load(codemap_id)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    # Generate share token
    share_token = str(uuid.uuid4())[:8]
    
    success = await storage.update_share_token(codemap_id, share_token, is_public=True)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate share token"
        )
    
    return {
        "share_token": share_token,
        "codemap_id": codemap_id,
        "is_public": True
    }


@router.get("/shared/{share_token}", response_model=Codemap)
async def get_shared_codemap(share_token: str):
    """
    Retrieve a codemap by share token.
    
    Args:
        share_token: The share token
        
    Returns:
        The codemap if found, public, and not expired
    """
    storage = CodemapStorage()
    codemap = await storage.get_by_share_token(share_token)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail="Shared codemap not found or expired"
        )
    
    if not codemap.is_public:
        raise HTTPException(
            status_code=403,
            detail="Codemap is not public"
        )
    
    return codemap


@router.get("/{codemap_id}/export/html")
async def export_codemap_html(codemap_id: str):
    """
    Export a codemap as standalone HTML.
    
    Args:
        codemap_id: The codemap ID
        
    Returns:
        HTML content
    """
    from fastapi.responses import HTMLResponse
    from api.codemap.renderer import HTMLExporter
    
    storage = CodemapStorage()
    codemap = await storage.load(codemap_id)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    exporter = HTMLExporter()
    html_content = exporter.export(codemap)
    
    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f'attachment; filename="codemap-{codemap_id}.html"'
        }
    )


@router.get("/{codemap_id}/export/json")
async def export_codemap_json(codemap_id: str):
    """
    Export a codemap graph as JSON.
    
    Args:
        codemap_id: The codemap ID
        
    Returns:
        JSON graph data
    """
    storage = CodemapStorage()
    codemap = await storage.load(codemap_id)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    return codemap.render.json_graph


@router.get("/{codemap_id}/export/mermaid")
async def export_codemap_mermaid(codemap_id: str):
    """
    Export a codemap as Mermaid diagram code.
    
    Args:
        codemap_id: The codemap ID
        
    Returns:
        Mermaid code as text
    """
    from fastapi.responses import PlainTextResponse
    
    storage = CodemapStorage()
    codemap = await storage.load(codemap_id)
    
    if not codemap:
        raise HTTPException(
            status_code=404,
            detail=f"Codemap {codemap_id} not found"
        )
    
    return PlainTextResponse(
        content=codemap.render.mermaid,
        media_type="text/plain"
    )
